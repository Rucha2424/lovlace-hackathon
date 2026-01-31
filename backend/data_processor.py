"""
Fronthaul data processing: load .dat files, normalize time, extract features,
and infer topology via correlated packet loss (cells on same link).
"""
import json
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering

from backend.config import (
    THROUGHPUT_DIR,
    PACKET_STATS_DIR,
    OUTPUT_DIR,
    SYMBOLS_PER_SLOT,
    SLOT_DURATION_US,
    NUM_CELLS,
    NUM_LINKS,
    ensure_dirs,
)


# --- Helpers ---
def _detect_delimiter(filepath: Path) -> str:
    """Detect delimiter (tab or comma) from first line."""
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        first = f.readline()
    if "\t" in first:
        return "\t"
    return ","


def _normalize_symbols_to_slots(symbols_series: pd.Series) -> pd.Series:
    """Convert symbol index to slot index (1 slot = 14 symbols)."""
    return (symbols_series / SYMBOLS_PER_SLOT).astype(int)


def load_throughput_file(filepath: Path) -> pd.DataFrame | None:
    """Load one throughput .dat file; return DataFrame with columns [slot, cell_id, throughput_bps] or similar."""
    try:
        delim = _detect_delimiter(filepath)
        df = pd.read_csv(filepath, sep=delim, header=None, skipinitialspace=True)
        # Expect at least: time/symbols, value (and optionally cell id in filename)
        if df.shape[1] < 2:
            return None
        df.columns = [f"col_{i}" for i in range(df.shape[1])]
        time_col = df.columns[0]
        value_col = df.columns[1]
        # Normalize time to slots if numeric
        if pd.api.types.is_numeric_dtype(df[time_col]):
            df["slot"] = _normalize_symbols_to_slots(pd.to_numeric(df[time_col], errors="coerce"))
        else:
            df["slot"] = np.arange(len(df)) // SYMBOLS_PER_SLOT
        df["throughput_raw"] = pd.to_numeric(df[value_col], errors="coerce").fillna(0)
        # Throughput in Gbps: raw can be bytes per symbol (e.g. sample .dat) -> bytes per slot = raw * SYMBOLS_PER_SLOT, then bps then Gbps
        bytes_per_slot = df["throughput_raw"] * SYMBOLS_PER_SLOT
        df["throughput_gbps"] = (bytes_per_slot * 8 / (SLOT_DURATION_US / 1e6)) / 1e9
        return df[["slot", "throughput_raw", "throughput_gbps"]].copy()
    except Exception:
        return None


def load_packet_stats_file(filepath: Path) -> pd.DataFrame | None:
    """Load one packet statistics .dat file."""
    try:
        delim = _detect_delimiter(filepath)
        df = pd.read_csv(filepath, sep=delim, header=None, skipinitialspace=True)
        if df.shape[1] < 2:
            return None
        df.columns = [f"col_{i}" for i in range(df.shape[1])]
        time_col = df.columns[0]
        # Assume columns: time, sent, lost (or similar)
        df["slot"] = _normalize_symbols_to_slots(pd.to_numeric(df[time_col], errors="coerce").fillna(0).astype(int))
        df["packets_sent"] = pd.to_numeric(df[df.columns[1]], errors="coerce").fillna(0)
        df["packets_lost"] = pd.to_numeric(df[df.columns[2]] if df.shape[1] > 2 else 0, errors="coerce").fillna(0)
        df["loss_rate"] = np.where(df["packets_sent"] > 0, df["packets_lost"] / df["packets_sent"], 0)
        return df[["slot", "packets_sent", "packets_lost", "loss_rate"]].copy()
    except Exception:
        return None


def extract_cell_id_from_filename(filename: str) -> int | None:
    """Extract cell number from filename e.g. cell_01.dat, throughput_5.dat -> 1, 5."""
    match = re.search(r"(?:cell[_\s]?|cell_id[_\s]?)?(\d{1,2})", filename, re.I)
    if match:
        return int(match.group(1)) % NUM_CELLS
    return None


def load_all_dat_files(
    throughput_dir: Path = THROUGHPUT_DIR,
    packet_dir: Path = PACKET_STATS_DIR,
) -> tuple[dict[int, pd.DataFrame], dict[int, pd.DataFrame]]:
    """Load all .dat files; return throughput_dfs and packet_dfs keyed by cell_id (0..23)."""
    throughput_dfs: dict[int, pd.DataFrame] = {}
    packet_dfs: dict[int, pd.DataFrame] = {}

    for d, keyed_dfs, loader in [
        (throughput_dir, throughput_dfs, load_throughput_file),
        (packet_dir, packet_dfs, load_packet_stats_file),
    ]:
        if not d.exists():
            continue
        for f in sorted(d.glob("*.dat")):
            cell_id = extract_cell_id_from_filename(f.name)
            if cell_id is None:
                cell_id = len(keyed_dfs) % NUM_CELLS
            df = loader(f)
            if df is not None and not df.empty:
                keyed_dfs[cell_id] = df

    return throughput_dfs, packet_dfs


def correlate_packet_loss(packet_dfs: dict[int, pd.DataFrame], num_slots: int = 120000) -> np.ndarray:
    """
    Build a matrix of loss-rate time series per cell (aligned by slot), then compute pairwise
    correlation. Cells on the same physical link tend to have correlated packet loss.
    """
    cell_ids = sorted(packet_dfs.keys())
    if len(cell_ids) < 2:
        return np.eye(NUM_CELLS)

    # Align to common slot range
    slot_min = max(df["slot"].min() for df in packet_dfs.values())
    slot_max = min(df["slot"].max() for df in packet_dfs.values())
    slots = np.arange(slot_min, min(slot_max + 1, slot_min + num_slots))

    matrix = np.full((len(cell_ids), len(slots)), np.nan)
    for i, cid in enumerate(cell_ids):
        df = packet_dfs[cid]
        by_slot = df.set_index("slot").reindex(slots)
        matrix[i, :] = by_slot["loss_rate"].values

    np.nan_to_num(matrix, copy=False, nan=0.0)
    corr = np.corrcoef(matrix)
    return np.nan_to_num(corr, nan=0.0, posinf=0.0, neginf=0.0)


def infer_topology_from_correlation(
    corr_matrix: np.ndarray,
    cell_ids: list[int],
    num_links: int = NUM_LINKS,
) -> dict[int, int]:
    """Assign each cell to a link (0..num_links-1) using correlation clustering (greedy)."""
    n = len(cell_ids)
    if n == 0:
        return {}
    # Use average correlation to others as affinity; cluster by similarity
    # Dissimilarity = 1 - correlation (so high corr = low distance)
    dist = 1 - np.clip(corr_matrix, 0, 1)
    np.fill_diagonal(dist, 0)
    clustering = AgglomerativeClustering(n_clusters=num_links, metric="precomputed", linkage="average")
    labels = clustering.fit_predict(dist)
    return {cell_ids[i]: int(labels[i]) for i in range(n)}


def aggregate_traffic_per_link(
    throughput_dfs: dict[int, pd.DataFrame],
    cell_to_link: dict[int, int],
    slot_range: tuple[int, int] | None = None,
    slot_step: int = 2000,
) -> list[dict[str, Any]]:
    """
    Aggregate throughput (Gbps) per link over time. Returns list of {slot, time_sec, link_1_gbps, link_2_gbps, link_3_gbps}.
    """
    if not throughput_dfs or not cell_to_link:
        return []

    all_slots = set()
    for df in throughput_dfs.values():
        all_slots.update(df["slot"].astype(int).tolist())
    slots = sorted(all_slots)
    if slot_range:
        slots = [s for s in slots if slot_range[0] <= s <= slot_range[1]]
    if not slots:
        return []

    slot_min, slot_max = min(slots), max(slots)
    # Downsample by slot_step for 60-second window: 60 * 2000 = 120000 slots -> step 2000 -> 60 points
    slots_sampled = list(range(slot_min, slot_max + 1, max(1, slot_step)))

    link_ids = sorted(set(cell_to_link.values()))
    result = []
    for slot in slots_sampled:
        time_sec = slot * SLOT_DURATION_US / 1e6
        sums = {lid: 0.0 for lid in link_ids}
        for cell_id, df in throughput_dfs.items():
            link_id = cell_to_link.get(cell_id, 0)
            row = df[df["slot"] == slot]
            if not row.empty:
                sums[link_id] += row["throughput_gbps"].iloc[0]
        result.append({
            "slot": slot,
            "time_sec": round(time_sec, 3),
            **{f"link_{lid+1}_gbps": round(sums[lid], 4) for lid in link_ids},
        })
    return result


def run_processing(
    throughput_dir: Path = THROUGHPUT_DIR,
    packet_dir: Path = PACKET_STATS_DIR,
    output_dir: Path = OUTPUT_DIR,
) -> dict[str, Any]:
    """Load data, infer topology, aggregate traffic; write JSON and return summary."""
    ensure_dirs()
    throughput_dfs, packet_dfs = load_all_dat_files(throughput_dir, packet_dir)

    # If no .dat files found, generate synthetic data for demo
    if not throughput_dfs and not packet_dfs:
        throughput_dfs, packet_dfs = generate_synthetic_data()

    cell_ids = sorted(set(throughput_dfs.keys()) | set(packet_dfs.keys()))
    if not cell_ids:
        cell_ids = list(range(NUM_CELLS))

    corr_matrix = correlate_packet_loss(packet_dfs) if packet_dfs else np.eye(len(cell_ids))
    cell_to_link = infer_topology_from_correlation(corr_matrix, cell_ids)

    # Build topology graph: DU -> Link 1,2,3 -> RU (group of cells) -> Cells
    topology = build_topology_graph(cell_to_link, cell_ids)

    aggregated = aggregate_traffic_per_link(
        throughput_dfs,
        cell_to_link,
        slot_range=None,
        slot_step=2000,
    )

    # Congestion summary per cell (e.g. 95th percentile throughput)
    congestion = {}
    for cid in cell_ids:
        if cid in throughput_dfs:
            df = throughput_dfs[cid]
            congestion[str(cid)] = {
                "p95_gbps": round(float(df["throughput_gbps"].quantile(0.95)), 4),
                "mean_gbps": round(float(df["throughput_gbps"].mean()), 4),
                "link_id": cell_to_link.get(cid, 0),
            }
        else:
            congestion[str(cid)] = {"p95_gbps": 0, "mean_gbps": 0, "link_id": cell_to_link.get(cid, 0)}

    # Total estimated link capacities (max over time)
    link_capacities = {}
    for rec in aggregated:
        for k, v in rec.items():
            if k.startswith("link_") and k.endswith("_gbps"):
                link_capacities[k] = max(link_capacities.get(k, 0), v)

    summary = {
        "topology": topology,
        "cell_to_link": {str(k): v for k, v in cell_to_link.items()},
        "aggregated_traffic": aggregated,
        "congestion": congestion,
        "link_capacities": link_capacities,
        "cell_ids": cell_ids,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "topology.json", "w") as f:
        json.dump(topology, f, indent=2)
    with open(output_dir / "aggregated_traffic.json", "w") as f:
        json.dump(aggregated, f, indent=2)
    with open(output_dir / "dashboard.json", "w") as f:
        json.dump({
            "congestion": congestion,
            "link_capacities": link_capacities,
            "cell_ids": cell_ids,
            "cell_to_link": summary["cell_to_link"],
        }, f, indent=2)
    with open(output_dir / "full_output.json", "w") as f:
        json.dump(summary, f, indent=2)
    return summary


def build_topology_graph(cell_to_link: dict[int, int], cell_ids: list[int]) -> dict[str, Any]:
    """Build DU -> Link -> RU -> Cell hierarchy for frontend graph."""
    links: dict[int, list[int]] = {}
    for cid, lid in cell_to_link.items():
        links.setdefault(lid, []).append(cid)
    nodes = [
        {"id": "DU", "type": "du", "label": "DU"},
    ]
    edges = []
    for lid in sorted(links.keys()):
        node_id = f"Link_{lid+1}"
        nodes.append({"id": node_id, "type": "link", "label": f"Link {lid+1}"})
        edges.append({"source": "DU", "target": node_id})
        ru_id = f"RU_{lid+1}"
        nodes.append({"id": ru_id, "type": "ru", "label": f"RU {lid+1}"})
        edges.append({"source": node_id, "target": ru_id})
        for cid in sorted(links[lid]):
            cell_node = f"Cell_{cid}"
            nodes.append({"id": cell_node, "type": "cell", "label": f"Cell {cid}"})
            edges.append({"source": ru_id, "target": cell_node})
    return {"nodes": nodes, "edges": edges}


def generate_synthetic_data() -> tuple[dict[int, pd.DataFrame], dict[int, pd.DataFrame]]:
    """Generate synthetic throughput and packet stats for 24 cells when no .dat files exist."""
    np.random.seed(42)
    throughput_dfs = {}
    packet_dfs = {}
    # 60 seconds * 2000 slots/s = 120000 slots; use 12000 for lighter synthetic
    num_slots = 12000
    slots = np.arange(num_slots)
    for cell_id in range(24):
        link_id = cell_id % NUM_LINKS
        base = 0.5 + link_id * 0.3 + np.random.rand() * 0.2
        trend = 0.1 * np.sin(slots / 500) + np.random.randn(num_slots) * 0.05
        throughput_dfs[cell_id] = pd.DataFrame({
            "slot": slots,
            "throughput_raw": np.clip(base + trend, 0.1, 2.0) * 1e8,
            "throughput_gbps": np.clip(base + trend, 0.1, 2.0),
        })
        loss_base = 0.002 + link_id * 0.001 + np.random.rand() * 0.002
        loss_noise = np.random.randn(num_slots) * 0.001
        loss_rate = np.clip(loss_base + loss_noise, 0, 0.05)
        packet_dfs[cell_id] = pd.DataFrame({
            "slot": slots,
            "packets_sent": np.random.poisson(1000, num_slots),
            "packets_lost": (loss_rate * 1000).astype(int),
            "loss_rate": loss_rate,
        })
    return throughput_dfs, packet_dfs


if __name__ == "__main__":
    result = run_processing()
    print("Cells:", result["cell_ids"])
    print("Link capacities:", result["link_capacities"])
    print("Output written to backend/output/")
