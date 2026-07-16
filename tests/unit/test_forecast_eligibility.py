from estate_intelligence.forecasting.eligibility import assess_eligibility
from estate_intelligence.forecasting.models import ForecastingConfig, ForecastSeries, SeriesPoint


def _config() -> ForecastingConfig:
    return ForecastingConfig.from_yaml(__import__("pathlib").Path("config/forecasting.yaml"))


def _series(values: list[float]) -> ForecastSeries:
    points = tuple(
        SeriesPoint(
            "s",
            "target",
            "estate",
            "estate",
            f"2025-{index + 1:02d}",
            value,
            1,
            "none",
            "observed",
            "{}",
        )
        for index, value in enumerate(values)
    )
    return ForecastSeries("s", "target", "estate", "estate", points)


def test_eligibility_detects_sparse_constant_and_eligible_series() -> None:
    config = _config()
    assert assess_eligibility(_series([0] * 24), config).eligibility_status == "inactive_series"
    assert assess_eligibility(_series([5] * 24), config).eligibility_status == "constant_series"
    assert (
        assess_eligibility(_series([1, 2, 3, 4, 5, 6] * 4), config).eligibility_status == "eligible"
    )
