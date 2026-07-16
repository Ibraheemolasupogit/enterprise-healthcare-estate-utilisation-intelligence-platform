"""Scenario risk and confidence helpers."""

from __future__ import annotations


def confidence_status(manual_reviews: int, capacity_margin: float) -> str:
    """Return conservative confidence status."""

    if manual_reviews >= 2:
        return "low"
    if capacity_margin < 0:
        return "insufficient_evidence"
    if capacity_margin < 0.1:
        return "moderate"
    return "high"
