"""Descriptive unit-cost metric helpers."""

from __future__ import annotations

from estate_intelligence.metrics.utilisation import safe_divide


def annual_operating_cost(row: dict[str, object], included_components: tuple[str, ...]) -> float:
    """Sum configured recurring operating-cost components."""

    total = 0.0
    for component in included_components:
        value = row.get(component)
        total += float(value) if isinstance(value, str | int | float) and value != "" else 0.0
    return total


def unit_cost(cost: float, denominator: float) -> float:
    """Return a descriptive unit cost."""

    return safe_divide(cost, denominator)
