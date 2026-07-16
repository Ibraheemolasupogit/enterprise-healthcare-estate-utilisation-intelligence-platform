"""Workforce metric helpers."""

from __future__ import annotations

from estate_intelligence.metrics.utilisation import bounded, safe_divide


def workforce_availability_ratio(available_fte: float, planned_fte: float) -> float:
    """Available FTE divided by planned FTE, bounded for scoring."""

    return bounded(safe_divide(available_fte, planned_fte))


def contacts_per_available_fte(completed_contacts: int, available_fte: float) -> float:
    """Completed contacts divided by available FTE."""

    return safe_divide(completed_contacts, available_fte)
