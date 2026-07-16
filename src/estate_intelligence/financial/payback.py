"""Payback helpers."""

from __future__ import annotations


def payback_year(cashflows: list[float], not_reached: str = "not_reached") -> str:
    cumulative = 0.0
    for index, value in enumerate(cashflows, start=1):
        cumulative += value
        if cumulative >= 0.0:
            return str(index)
    return not_reached
