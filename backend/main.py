"""
FastAPI backend for Intelligent Fronthaul Network Optimization.
Serves topology, traffic, dashboard, and capacity estimation.
"""
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from backend.config import OUTPUT_DIR, ensure_dirs
from backend.data_processor import run_processing
from backend.capacity_estimator import estimate_all_links, estimate_link_capacity_gbps

app = FastAPI(
    title="Fronthaul Network Optimization API",
    description="API for topology, traffic, and capacity estimation",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _read_json(name: str) -> Any:
    path = OUTPUT_DIR / f"{name}.json"
    if not path.exists():
        return None
    import json
    with open(path, "r") as f:
        return json.load(f)


@app.on_event("startup")
def startup():
    ensure_dirs()
    # Precompute data if not present
    if not (OUTPUT_DIR / "dashboard.json").exists():
        run_processing()


@app.get("/")
def root():
    return {"message": "Fronthaul Network Optimization API", "docs": "/docs"}


@app.post("/api/process")
def process_data():
    """Re-run data processing (load .dat files, infer topology, aggregate traffic)."""
    result = run_processing()
    return {"status": "ok", "cells": len(result["cell_ids"]), "link_capacities": result["link_capacities"]}


@app.get("/api/topology")
def get_topology():
    """Return DU -> Link -> RU -> Cell graph for visualization."""
    data = _read_json("topology")
    if data is None:
        run_processing()
        data = _read_json("topology")
    return data or {"nodes": [], "edges": []}


@app.get("/api/traffic")
def get_traffic():
    """Return aggregated traffic per link over time (60s window)."""
    data = _read_json("aggregated_traffic")
    if data is None:
        run_processing()
        data = _read_json("aggregated_traffic")
    return data or []


@app.get("/api/dashboard")
def get_dashboard():
    """Dashboard: congestion per cell, link capacities, cell-to-link mapping."""
    data = _read_json("dashboard")
    if data is None:
        run_processing()
        data = _read_json("dashboard")
    return data or {"congestion": {}, "link_capacities": {}, "cell_ids": [], "cell_to_link": {}}


@app.get("/api/capacity")
def get_capacity(with_buffer: bool = Query(True, description="Include buffer (4 symbols / 143 μs)")):
    """Capacity estimates per link: with and without buffer, 1% packet loss budget."""
    dash = _read_json("dashboard")
    if dash is None:
        run_processing()
        dash = _read_json("dashboard")
    link_caps = dash.get("link_capacities", {}) if dash else {}
    estimates = estimate_all_links(link_caps, with_buffer=with_buffer)
    return {"with_buffer": with_buffer, "estimates": estimates, "link_capacities": link_caps}


@app.get("/api/reports")
def get_reports():
    """Summary for judging: innovations and technical feasibility."""
    return {
        "innovations": [
            "Correlation-based topology inference from packet loss (no manual labeling).",
            "Time normalization: symbols → slots (1 slot = 14 symbols = 500 μs).",
            "Aggregated traffic per link over 60-second window for congestion visibility.",
            "Capacity estimator with buffer (4 symbols / 143 μs) vs no-buffer and 1% packet loss budget.",
        ],
        "tech_stack": [
            "Backend: Python, FastAPI, Pandas, NumPy, Scikit-learn, NetworkX",
            "Frontend: React, Tailwind CSS, Recharts, React Flow",
            "Data: .dat files (throughput + packet stats) → JSON export",
        ],
        "feasibility": "Pipeline runs on 48 .dat files (24 throughput, 24 packet stats); topology and traffic JSON served via API; dashboard and topology map ready for hackathon demo.",
    }
