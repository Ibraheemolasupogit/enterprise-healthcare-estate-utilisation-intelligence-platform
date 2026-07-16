"""Deterministic model selection."""

from __future__ import annotations

from estate_intelligence.forecasting.models import ModelResult, SelectionResult

SIMPLICITY_ORDER = {
    "naive": 0,
    "seasonal_naive": 1,
    "moving_average": 2,
    "drift": 3,
    "simple_exponential_smoothing": 4,
    "holt_linear": 5,
    "holt_winters_additive": 6,
}


def select_model(
    series_id: str,
    results: list[ModelResult],
    primary_metric: str,
    baseline_model_id: str = "naive",
    tolerance: float = 0.000001,
) -> SelectionResult:
    """Select the lowest-error model with deterministic simpler-model tie breaking."""

    successful = [
        result
        for result in results
        if result.model_status == "evaluated" and result.metrics.get(primary_metric) is not None
    ]
    if not successful:
        return SelectionResult(
            series_id=series_id,
            selected_model_id=baseline_model_id,
            primary_metric=primary_metric,
            primary_metric_value=None,
            baseline_model_id=baseline_model_id,
            baseline_metric_value=None,
            baseline_beaten_flag=False,
            selection_reason="no evaluated model had defined primary metric",
        )
    metric_values: dict[str, float] = {}
    for result in successful:
        value = result.metrics[primary_metric]
        if value is not None:
            metric_values[result.model_id] = float(value)
    best_metric = min(metric_values.values())
    candidates = [
        result for result in successful if metric_values[result.model_id] <= best_metric + tolerance
    ]
    selected = sorted(
        candidates,
        key=lambda result: (SIMPLICITY_ORDER.get(result.model_id, 99), result.model_id),
    )[0]
    baseline = next((result for result in successful if result.model_id == baseline_model_id), None)
    baseline_metric = None
    if baseline is not None:
        baseline_value = baseline.metrics[primary_metric]
        if baseline_value is not None:
            baseline_metric = float(baseline_value)
    selected_value = selected.metrics[primary_metric]
    selected_metric = float(selected_value) if selected_value is not None else best_metric
    return SelectionResult(
        series_id=series_id,
        selected_model_id=selected.model_id,
        primary_metric=primary_metric,
        primary_metric_value=selected_metric,
        baseline_model_id=baseline_model_id,
        baseline_metric_value=baseline_metric,
        baseline_beaten_flag=baseline_metric is not None and selected_metric < baseline_metric,
        selection_reason="lowest primary metric with simpler-model tie break",
    )
