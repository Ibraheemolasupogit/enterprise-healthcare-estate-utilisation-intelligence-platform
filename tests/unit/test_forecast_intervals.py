from estate_intelligence.forecasting.intervals import build_intervals, coverage


def test_intervals_clip_lower_bound_and_calculate_coverage() -> None:
    rows = build_intervals([1.0], [5.0], (0.8,))
    assert rows[0]["lower_bound"] == 0.0
    assert coverage([1.0], [1.0], [0.0], 0.8) == 1.0
