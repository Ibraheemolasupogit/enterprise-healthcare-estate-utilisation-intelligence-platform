"""Discounting and NPV helpers."""

from __future__ import annotations


def discount_factor(rate: float, year: int) -> float:
    return 1.0 / ((1.0 + rate) ** year)


def net_present_value(cashflows: list[float], rate: float) -> float:
    return sum(
        value * discount_factor(rate, index) for index, value in enumerate(cashflows, start=1)
    )
