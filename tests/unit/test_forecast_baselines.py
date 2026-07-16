import pytest

from estate_intelligence.forecasting.baseline import drift, moving_average, naive, seasonal_naive


def test_baseline_models_are_deterministic_and_non_negative() -> None:
    assert naive([1, 2, 3], 2) == [3, 3]
    assert moving_average([1, 2, 3], 2, 2) == [2.5, 2.5]
    assert drift([10, 7], 2) == [4, 1]
    assert seasonal_naive(list(range(1, 13)), 3, 12) == [1, 2, 3]


def test_seasonal_naive_requires_history() -> None:
    with pytest.raises(ValueError):
        seasonal_naive([1, 2], 1, 12)
