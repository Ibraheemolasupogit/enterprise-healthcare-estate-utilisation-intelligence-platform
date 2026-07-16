from estate_intelligence.forecasting.exponential_smoothing import (
    holt_linear,
    holt_winters_additive,
    simple_exponential_smoothing,
)


def test_exponential_smoothing_forecasts_have_requested_horizon() -> None:
    assert len(simple_exponential_smoothing([10, 12, 14], 3)) == 3
    assert len(holt_linear([10, 12, 14, 16], 2)) == 2
    assert len(holt_winters_additive([10, 11] * 12, 4, 12)) == 4
