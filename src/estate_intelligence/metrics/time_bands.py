"""Deterministic time-band assignment."""

from __future__ import annotations

from datetime import time

from estate_intelligence.metrics.models import TimeBand


def parse_time(value: str) -> time:
    """Parse HH:MM text."""

    hour, minute = value.split(":")
    return time(hour=int(hour), minute=int(minute))


def assign_time_band(value: str, bands: dict[str, TimeBand]) -> str:
    """Assign a time to exactly one configured band."""

    current = parse_time(value)
    for name, band in bands.items():
        if parse_time(band.start) <= current < parse_time(band.end):
            return name
    raise ValueError(f"time {value} falls outside configured bands")


def is_peak_band(name: str, bands: dict[str, TimeBand]) -> bool:
    """Return whether a configured band is peak."""

    return bands[name].peak
