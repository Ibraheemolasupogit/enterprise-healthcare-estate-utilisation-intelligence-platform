from estate_intelligence.simulation.results import normal_ci


def test_confidence_interval_handles_single_and_multiple_values() -> None:
    assert normal_ci([3.0], 0.95) == (3.0, 3.0)
    low, high = normal_ci([1.0, 2.0, 3.0], 0.95)

    assert low < 2.0 < high
