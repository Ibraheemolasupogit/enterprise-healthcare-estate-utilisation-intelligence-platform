from estate_intelligence.simulation.results import percentile, status_from_thresholds


def test_percentiles_and_statuses_are_stable() -> None:
    assert percentile([1, 2, 3, 4], 0.5) == 2.5
    assert round(percentile([1, 2, 3, 4, 5], 0.95), 4) == 4.8
    assert status_from_thresholds(0) == "pass"
    assert status_from_thresholds(1) == "fail"
