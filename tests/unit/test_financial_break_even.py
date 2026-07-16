from estate_intelligence.financial.break_even import (
    maximum_mitigation_before_negative,
    maximum_transition_cost_for_zero_npv,
    minimum_annual_effect_for_payback,
)


def test_break_even_calculations() -> None:
    assert round(maximum_transition_cost_for_zero_npv([100.0, 100.0], 0.0), 4) == 200.0
    assert minimum_annual_effect_for_payback(500.0, 5) == 100.0
    assert maximum_mitigation_before_negative(250.0) == 250.0
