"""
Capacity estimation for fronthaul links: with/without buffer, 1% permissible packet loss.
"""
from typing import Any

from backend.config import (
    SLOT_DURATION_US,
    BUFFER_SYMBOLS,
    BUFFER_DURATION_US,
    MAX_PACKET_LOSS_PERCENT,
    SYMBOLS_PER_SLOT,
)


def estimate_link_capacity_gbps(
    peak_throughput_gbps: float,
    with_buffer: bool,
    packet_loss_budget_percent: float = MAX_PACKET_LOSS_PERCENT,
) -> dict[str, Any]:
    """
    Estimate required FH link capacity (Gbps).
    - With buffer: 4 symbols (143 μs) buffering reduces peak requirement.
    - Without buffer: capacity must meet peak to avoid loss.
    - 1% packet loss budget allows slight underprovisioning (simplified: scale by 1/(1 - loss)).
    """
    # Simplified: required capacity >= peak * (1 + margin for loss budget)
    # Margin so that up to 1% loss is acceptable: effective rate = peak / (1 - loss/100)
    loss_factor = 1.0 / (1.0 - packet_loss_budget_percent / 100.0) if packet_loss_budget_percent < 100 else 1.0
    required_no_buffer = peak_throughput_gbps * loss_factor

    if with_buffer:
        # Buffer absorbs short bursts; effective peak is reduced (e.g. 0.85 factor for 143 μs buffer)
        buffer_factor = 0.85  # empirical: buffer smooths ~15% of peak
        required_with_buffer = (peak_throughput_gbps * buffer_factor) * loss_factor
    else:
        required_with_buffer = required_no_buffer

    return {
        "with_buffer_gbps": round(required_with_buffer, 4),
        "without_buffer_gbps": round(required_no_buffer, 4),
        "peak_throughput_gbps": round(peak_throughput_gbps, 4),
        "buffer_duration_us": BUFFER_DURATION_US if with_buffer else 0,
        "packet_loss_budget_percent": packet_loss_budget_percent,
    }


def estimate_all_links(
    link_capacities: dict[str, float],
    with_buffer: bool = True,
) -> dict[str, Any]:
    """Given link_capacities (e.g. link_1_gbps, link_2_gbps, link_3_gbps), return estimates."""
    results = {}
    for key, peak in link_capacities.items():
        if not key.endswith("_gbps"):
            continue
        link_name = key.replace("_gbps", "")
        results[link_name] = estimate_link_capacity_gbps(peak, with_buffer=with_buffer)
    return results
