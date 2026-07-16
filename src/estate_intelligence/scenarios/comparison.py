"""Scenario scoring helpers."""

from __future__ import annotations


def bounded(value: float) -> float:
    """Bound a score dimension to 0-1."""

    return max(0.0, min(1.0, value))


def score_dimensions(
    *,
    capacity_margin: float,
    workforce_ok: bool,
    accessibility_ok: bool,
    cost_difference: float,
    burden: float,
    confidence: str,
    risk_count: int,
    weights: dict[str, float],
) -> list[dict[str, float | str]]:
    """Build weighted comparison dimensions."""

    confidence_value = {"high": 1.0, "moderate": 0.75, "low": 0.45}.get(confidence, 0.25)
    raw = {
        "capacity": bounded(0.5 + capacity_margin),
        "service_continuity": bounded(1.0 - burden),
        "workforce": 1.0 if workforce_ok else 0.5,
        "accessibility": 1.0 if accessibility_ok else 0.5,
        "recurring_cost": bounded(0.5 + (-cost_difference / 1_000_000)),
        "implementation_burden": bounded(1.0 - burden),
        "data_confidence": confidence_value,
        "risk": bounded(1.0 - risk_count * 0.2),
    }
    return [
        {
            "dimension": dimension,
            "raw_value": round(value, 4),
            "weight": weights[dimension],
            "weighted_score": round(value * weights[dimension], 4),
        }
        for dimension, value in sorted(raw.items())
    ]
