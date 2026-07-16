"""Clinical activity metric helpers."""

from __future__ import annotations

from estate_intelligence.metrics.utilisation import safe_divide


def completion_rate(completed_contacts: int, scheduled_contacts: int) -> float:
    """Completed contacts divided by scheduled contacts."""

    return safe_divide(completed_contacts, scheduled_contacts)


def contacts_per_hour(completed_contacts: int, hours: float) -> float:
    """Completed contacts per room hour."""

    return safe_divide(completed_contacts, hours)
