from estate_intelligence.simulation.validation import threshold_status


def test_threshold_direction_is_explicit() -> None:
    assert threshold_status("minimum_completion_rate", 0.95, 0.92) == "pass"
    assert threshold_status("minimum_completion_rate", 0.8, 0.92) == "fail"
    assert threshold_status("maximum_mean_wait_minutes", 10, 20) == "pass"
    assert threshold_status("maximum_mean_wait_minutes", 25, 20) == "fail"
