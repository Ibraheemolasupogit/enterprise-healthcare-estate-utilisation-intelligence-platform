"""Break-even calculations."""

from __future__ import annotations

from estate_intelligence.financial.npv import discount_factor


def maximum_transition_cost_for_zero_npv(
    annual_effects: list[float], discount_rate: float
) -> float:
    return sum(
        value * discount_factor(discount_rate, year)
        for year, value in enumerate(annual_effects, start=1)
    )


def minimum_annual_effect_for_payback(transition_cost: float, years: int) -> float:
    if years <= 0:
        return 0.0
    return transition_cost / years


def maximum_mitigation_before_negative(gross_effect: float) -> float:
    return max(0.0, gross_effect)
