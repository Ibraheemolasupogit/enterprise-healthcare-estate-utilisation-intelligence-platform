from estate_intelligence.metrics.workforce import (
    contacts_per_available_fte,
    workforce_availability_ratio,
)


def test_workforce_metrics_are_bounded_and_zero_safe() -> None:
    assert workforce_availability_ratio(8, 10) == 0.8
    assert workforce_availability_ratio(12, 10) == 1.0
    assert contacts_per_available_fte(100, 5) == 20
    assert contacts_per_available_fte(100, 0) == 0
