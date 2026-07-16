from estate_intelligence.metrics.utilisation import (
    actual_occupied_utilisation,
    attendance_utilisation,
    booked_utilisation,
    safe_divide,
)


def test_utilisation_formulas_are_bounded_and_zero_safe() -> None:
    assert booked_utilisation(5, 10) == 0.5
    assert actual_occupied_utilisation(12, 10) == 1.0
    assert attendance_utilisation(7, 10) == 0.7
    assert safe_divide(1, 0) == 0
