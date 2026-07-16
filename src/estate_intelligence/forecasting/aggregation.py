"""Monthly demand aggregation helpers."""

from __future__ import annotations

from datetime import date


def month_keys(start: str, end: str) -> list[str]:
    """Return complete monthly period keys between two ISO dates."""

    start_date = date.fromisoformat(start)
    end_date = date.fromisoformat(end)
    current = date(start_date.year, start_date.month, 1)
    keys: list[str] = []
    while current <= end_date:
        keys.append(f"{current.year:04d}-{current.month:02d}")
        current = date(
            current.year + (1 if current.month == 12 else 0),
            1 if current.month == 12 else current.month + 1,
            1,
        )
    return keys


def next_months(last_period: str, horizon: int) -> list[str]:
    """Return future monthly period labels after the last historical period."""

    year, month = (int(part) for part in last_period.split("-"))
    periods: list[str] = []
    for _ in range(horizon):
        if month == 12:
            year += 1
            month = 1
        else:
            month += 1
        periods.append(f"{year:04d}-{month:02d}")
    return periods


def room_hours(face_to_face_contacts: float, average_duration_minutes: float) -> float:
    """Derive face-to-face room-hour demand from contacts and duration."""

    return face_to_face_contacts * average_duration_minutes / 60
