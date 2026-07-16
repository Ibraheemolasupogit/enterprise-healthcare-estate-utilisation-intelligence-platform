from estate_intelligence.metrics.scoring import persistent_underutilisation_flag


def test_persistent_underutilisation_requires_window_and_observations() -> None:
    assert persistent_underutilisation_flag(4, 6, 4, 3) is True
    assert persistent_underutilisation_flag(3, 6, 4, 3) is False
    assert persistent_underutilisation_flag(4, 2, 4, 3) is False
