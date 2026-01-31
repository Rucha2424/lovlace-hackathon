"""Configuration for fronthaul data paths and constants."""
import os
from pathlib import Path

# Paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = PROJECT_ROOT / "data"
THROUGHPUT_DIR = DATA_ROOT / "throughput"
PACKET_STATS_DIR = DATA_ROOT / "packet_stats"
OUTPUT_DIR = PROJECT_ROOT / "backend" / "output"

# Time constants (3GPP fronthaul)
SYMBOLS_PER_SLOT = 14
SLOT_DURATION_US = 500  # microseconds
SLOTS_PER_SECOND = 2000  # 1e6 / 500
BUFFER_SYMBOLS = 4
BUFFER_DURATION_US = 143  # 4 symbols ≈ 143 μs

# Capacity estimation
MAX_PACKET_LOSS_PERCENT = 1.0  # 1% permissible per cell
NUM_CELLS = 24
NUM_LINKS = 3  # Link 1, 2, 3
CELLS_PER_LINK = NUM_CELLS // NUM_LINKS  # 8

def ensure_dirs():
    """Create data and output directories if they don't exist."""
    for d in (THROUGHPUT_DIR, PACKET_STATS_DIR, OUTPUT_DIR):
        d.mkdir(parents=True, exist_ok=True)
