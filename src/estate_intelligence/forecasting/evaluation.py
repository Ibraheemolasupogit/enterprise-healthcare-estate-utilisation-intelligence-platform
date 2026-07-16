"""Forecast accuracy metrics."""

from __future__ import annotations

import math


def mae(actuals: list[float], forecasts: list[float]) -> float | None:
    """Mean absolute error."""

    if not actuals:
        return None
    return sum(abs(a - f) for a, f in zip(actuals, forecasts, strict=True)) / len(actuals)


def rmse(actuals: list[float], forecasts: list[float]) -> float | None:
    """Root mean squared error."""

    if not actuals:
        return None
    return math.sqrt(
        sum((a - f) ** 2 for a, f in zip(actuals, forecasts, strict=True)) / len(actuals)
    )


def wape(actuals: list[float], forecasts: list[float]) -> float | None:
    """Weighted absolute percentage error with explicit zero denominator handling."""

    denominator = sum(abs(a) for a in actuals)
    if denominator == 0:
        return None
    return sum(abs(a - f) for a, f in zip(actuals, forecasts, strict=True)) / denominator


def bias(actuals: list[float], forecasts: list[float]) -> float | None:
    """Signed average forecast error."""

    if not actuals:
        return None
    return sum(f - a for a, f in zip(actuals, forecasts, strict=True)) / len(actuals)


def signed_percentage_bias(actuals: list[float], forecasts: list[float]) -> float | None:
    """Signed bias as a share of actual demand where defined."""

    denominator = sum(actuals)
    if denominator == 0:
        return None
    return sum(f - a for a, f in zip(actuals, forecasts, strict=True)) / denominator


def smape(actuals: list[float], forecasts: list[float]) -> float | None:
    """Zero-safe symmetric mean absolute percentage error."""

    if not actuals:
        return None
    terms = []
    for actual, forecast in zip(actuals, forecasts, strict=True):
        denominator = abs(actual) + abs(forecast)
        terms.append(0.0 if denominator == 0 else 2 * abs(forecast - actual) / denominator)
    return sum(terms) / len(terms)


def mase(
    actuals: list[float], forecasts: list[float], training_values: list[float]
) -> float | None:
    """Mean absolute scaled error where a naive denominator exists."""

    absolute = mae(actuals, forecasts)
    if absolute is None or len(training_values) < 2:
        return None
    denominator = sum(
        abs(training_values[index] - training_values[index - 1])
        for index in range(1, len(training_values))
    ) / (len(training_values) - 1)
    if denominator == 0:
        return None
    return absolute / denominator


def metric_bundle(
    actuals: list[float], forecasts: list[float], training_values: list[float]
) -> dict[str, float | None]:
    """Return the configured core metric bundle."""

    return {
        "mae": mae(actuals, forecasts),
        "rmse": rmse(actuals, forecasts),
        "wape": wape(actuals, forecasts),
        "bias": bias(actuals, forecasts),
        "signed_percentage_bias": signed_percentage_bias(actuals, forecasts),
        "smape": smape(actuals, forecasts),
        "mase": mase(actuals, forecasts, training_values),
    }
