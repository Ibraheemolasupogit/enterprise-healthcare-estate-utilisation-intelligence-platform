"""Available-hours calculations."""

from __future__ import annotations

from datetime import date


def applicable_weeks(start_date: date, end_date: date) -> float:
    """Return inclusive weeks in an analysis period."""

    return ((end_date - start_date).days + 1) / 7


def available_room_hours(hours_per_week: float, weeks: float, active: bool = True) -> float:
    """Calculate configured available room hours."""

    return hours_per_week * weeks if active else 0.0
