"""Core utilisation formulas."""

from __future__ import annotations


def safe_divide(numerator: float, denominator: float) -> float:
    """Return a deterministic zero-safe ratio."""

    if denominator <= 0:
        return 0.0
    return numerator / denominator


def bounded(value: float) -> float:
    """Bound a metric between 0 and 1."""

    return max(0.0, min(1.0, value))


def booked_utilisation(booked_hours: float, available_hours: float) -> float:
    """Booked room hours divided by available room hours."""

    return bounded(safe_divide(booked_hours, available_hours))


def actual_occupied_utilisation(occupied_hours: float, available_hours: float) -> float:
    """Occupied room hours divided by available room hours."""

    return bounded(safe_divide(occupied_hours, available_hours))


def attendance_utilisation(actual_attendance: float, planned_attendance: float) -> float:
    """Actual attendance divided by planned attendance."""

    return bounded(safe_divide(actual_attendance, planned_attendance))


def effective_utilisation_score(components: dict[str, float], weights: dict[str, float]) -> float:
    """Weighted bounded effective clinical utilisation score."""

    return bounded(
        sum(bounded(components.get(name, 0.0)) * weight for name, weight in weights.items())
    )
