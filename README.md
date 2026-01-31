# Intelligent Fronthaul Network Optimization

Full-stack application for processing high-resolution telecommunications data to identify network topologies and estimate link capacities. Uses 48 `.dat` files (24 throughput + 24 packet statistics) with optional synthetic data when files are not present.

## Tech Stack

- **Backend:** Python (FastAPI), Pandas, NumPy, Scikit-learn, NetworkX
- **Frontend:** React, Tailwind CSS, React Flow, Recharts
- **Data:** Local `.dat` files → JSON export; topology inferred via correlated packet loss

## Project Structure

```
lovlace-hackathon/
├── backend/
│   ├── main.py           # FastAPI app, /api/topology, /api/traffic, /api/dashboard, /api/capacity, /api/reports
│   ├── data_processor.py # Load .dat, normalize time, infer topology, aggregate traffic
│   ├── capacity_estimator.py # With/without buffer, 1% packet loss
│   ├── config.py
│   └── output/           # Generated topology.json, aggregated_traffic.json, dashboard.json
├── frontend/             # React + Vite + Tailwind
│   └── src/
│       ├── pages/        # Dashboard, TopologyMap, TrafficAnalysis, CapacityEstimator, Reports
│       └── api/client.js
├── data/
│   ├── throughput/       # 24 × .dat (throughput per cell)
│   └── packet_stats/     # 24 × .dat (packet stats per cell)
└── scripts/
    └── generate_sample_dat.py  # Generate sample .dat files for dev
```

## Quick Start

### 1. Backend (from project root)

```bash
# Create venv (optional)
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

pip install -r backend/requirements.txt

# Optional: generate sample .dat files
python scripts/generate_sample_dat.py

# Run data processing (writes backend/output/*.json); or let API run it on first request
python -c "from backend.data_processor import run_processing; run_processing()"

# Start API (from project root)
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**. The Vite dev server proxies `/api` to `http://127.0.0.1:8000`.

## Data Format

- **Throughput `.dat`:** Tab- or comma-delimited; first column = time/symbols, second = throughput (bytes or rate). Script normalizes to slots (1 slot = 14 symbols = 500 μs) and computes Gbps per slot.
- **Packet stats `.dat`:** Tab- or comma-delimited; columns = time, packets_sent, packets_lost. Used to compute loss rate and correlate across cells to infer which cells share a link.

Place files in `data/throughput/` and `data/packet_stats/` with names like `throughput_cell_00.dat`, `packet_stats_cell_00.dat` (cell index 0–23).

## Features

- **Dashboard:** 24 cells, congestion (p95 Gbps), link capacities, cell-to-link mapping.
- **Topology Map:** DU → Link → RU → Cell graph (React Flow); links inferred from correlated packet loss.
- **Traffic Analysis:** Aggregated traffic per link over time (Recharts).
- **Capacity Estimator:** Toggle “With Buffer” (4 symbols / 143 μs) vs “Without Buffer”; 1% packet loss budget.
- **Reports:** Innovations and technical feasibility summary for judging.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/topology | DU → Link → RU → Cell graph (nodes, edges) |
| GET | /api/traffic | Aggregated traffic per link over time |
| GET | /api/dashboard | Congestion, link capacities, cell_to_link |
| GET | /api/capacity?with_buffer=true | Capacity estimates per link |
| GET | /api/reports | Innovations, tech stack, feasibility |
| POST | /api/process | Re-run data processing |

## License

MIT
