"""
Generate sample .dat files (24 throughput + 24 packet stats) for development.
Place output in data/throughput and data/packet_stats.
"""
import os
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
THROUGHPUT_DIR = PROJECT_ROOT / "data" / "throughput"
PACKET_DIR = PROJECT_ROOT / "data" / "packet_stats"
SYMBOLS_PER_SLOT = 14
NUM_SLOTS = 12000  # ~6 sec at 2000 slots/s

def main():
    THROUGHPUT_DIR.mkdir(parents=True, exist_ok=True)
    PACKET_DIR.mkdir(parents=True, exist_ok=True)
    np.random.seed(42)
    for cell_id in range(24):
        link_id = cell_id % 3
        slots = np.arange(NUM_SLOTS)
        base_gbps = 0.5 + link_id * 0.3 + np.random.rand() * 0.2
        trend = 0.1 * np.sin(slots / 500) + np.random.randn(NUM_SLOTS) * 0.05
        throughput_gbps = np.clip(base_gbps + trend, 0.1, 2.0)
        symbols = slots * SYMBOLS_PER_SLOT
        bytes_per_symbol = (throughput_gbps * 1e9 / 8) * (500e-6 / SYMBOLS_PER_SLOT)  # 500 us per slot
        th = np.column_stack([symbols, bytes_per_symbol])
        np.savetxt(THROUGHPUT_DIR / f"throughput_cell_{cell_id:02d}.dat", th, fmt="%.2f", delimiter="\t")
        loss_base = 0.002 + link_id * 0.001 + np.random.rand() * 0.002
        loss_rate = np.clip(loss_base + np.random.randn(NUM_SLOTS) * 0.001, 0, 0.05)
        sent = np.random.poisson(1000, NUM_SLOTS)
        lost = (loss_rate * sent).astype(int)
        ps = np.column_stack([symbols, sent, lost])
        np.savetxt(PACKET_DIR / f"packet_stats_cell_{cell_id:02d}.dat", ps, fmt="%d", delimiter="\t")
    print(f"Generated 24 throughput and 24 packet_stats .dat files in {PROJECT_ROOT / 'data'}")

if __name__ == "__main__":
    main()
