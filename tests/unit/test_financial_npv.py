from estate_intelligence.financial.npv import discount_factor, net_present_value


def test_npv_known_values_positive_negative_and_zero() -> None:
    assert round(discount_factor(0.10, 1), 4) == 0.9091
    assert round(net_present_value([110.0], 0.10), 4) == 100.0
    assert net_present_value([-100.0, -50.0], 0.10) < 0
    assert net_present_value([0.0], 0.10) == 0.0
