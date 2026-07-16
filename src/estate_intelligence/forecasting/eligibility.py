"""Forecast-series eligibility assessment."""

from __future__ import annotations

from statistics import mean, variance

from estate_intelligence.forecasting.models import (
    EligibilityResult,
    ForecastingConfig,
    ForecastSeries,
)


def assess_eligibility(series: ForecastSeries, config: ForecastingConfig) -> EligibilityResult:
    """Assess whether a series should receive statistical forecasting models."""

    values = series.values
    periods = len(values)
    non_zero_positions = [index for index, value in enumerate(values) if value != 0]
    non_zero = len(non_zero_positions)
    missing = sum(1 for point in series.points if point.imputation_flag != "observed")
    missing_ratio = missing / periods if periods else 1.0
    recent_activity = any(value > 0 for value in values[-3:])
    var = variance(values) if len(values) > 1 else 0.0
    non_zero_ratio = non_zero / periods if periods else 0.0
    intervals = [
        non_zero_positions[index] - non_zero_positions[index - 1]
        for index in range(1, len(non_zero_positions))
    ]
    average_interval = sum(intervals) / len(intervals) if intervals else None
    positive_values = [value for value in values if value > 0]
    squared_cv = None
    if len(positive_values) > 1 and mean(positive_values) != 0:
        squared_cv = (variance(positive_values) ** 0.5 / mean(positive_values)) ** 2

    status = "eligible"
    reason = "series meets configured eligibility thresholds"
    if periods < config.minimum_history_periods:
        status = "insufficient_history"
        reason = "series has fewer periods than minimum_history_periods"
    elif missing_ratio > config.maximum_missing_period_ratio:
        status = "quality_blocked"
        reason = "missing-period ratio exceeds configured maximum"
    elif non_zero == 0 or not recent_activity:
        status = "inactive_series"
        reason = "series has no recent non-zero activity"
    elif non_zero < config.minimum_non_zero_periods:
        status = "too_sparse"
        reason = "series has fewer non-zero periods than minimum_non_zero_periods"
    elif var == 0:
        status = "constant_series"
        reason = "series has no historical variance"
    elif (
        average_interval is not None
        and average_interval > config.intermittency_thresholds["baseline_only_average_interval"]
    ):
        status = "baseline_only"
        reason = "series is intermittent and restricted to baseline models"

    return EligibilityResult(
        series_id=series.series_id,
        target=series.target,
        entity_type=series.entity_type,
        entity_id=series.entity_id,
        eligibility_status=status,  # type: ignore[arg-type]
        reason=reason,
        historical_periods=periods,
        non_zero_periods=non_zero,
        missing_period_ratio=round(missing_ratio, 6),
        variance=round(var, 6),
        non_zero_ratio=round(non_zero_ratio, 6),
        average_interval_between_non_zero_periods=(
            round(average_interval, 6) if average_interval is not None else None
        ),
        squared_coefficient_of_variation=round(squared_cv, 6) if squared_cv is not None else None,
        recent_activity_flag=recent_activity,
    )
