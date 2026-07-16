from estate_intelligence.metrics.activity import completion_rate, contacts_per_hour


def test_activity_rates_are_zero_safe() -> None:
    assert completion_rate(8, 10) == 0.8
    assert completion_rate(1, 0) == 0
    assert contacts_per_hour(20, 4) == 5
