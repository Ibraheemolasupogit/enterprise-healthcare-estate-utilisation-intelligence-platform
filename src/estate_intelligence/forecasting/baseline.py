"""Transparent deterministic baseline forecasting models."""

from __future__ import annotations


def naive(values: list[float], horizon: int) -> list[float]:
    """Repeat the most recent observation."""

    last = values[-1] if values else 0.0
    return [max(0.0, last) for _ in range(horizon)]


def seasonal_naive(values: list[float], horizon: int, seasonal_period: int) -> list[float]:
    """Repeat the same season from the previous cycle."""

    if len(values) < seasonal_period:
        raise ValueError("seasonal naive requires one complete seasonal cycle")
    forecasts = []
    for step in range(horizon):
        index = len(values) - seasonal_period + (step % seasonal_period)
        forecasts.append(max(0.0, values[index]))
    return forecasts


def moving_average(values: list[float], horizon: int, window: int) -> list[float]:
    """Repeat a trailing moving average."""

    if window < 1:
        raise ValueError("moving average window must be positive")
    subset = values[-window:] if len(values) >= window else values
    average = sum(subset) / len(subset) if subset else 0.0
    return [max(0.0, average) for _ in range(horizon)]


def drift(values: list[float], horizon: int) -> list[float]:
    """Linear drift from first to last observation."""

    if len(values) < 2:
        return naive(values, horizon)
    slope = (values[-1] - values[0]) / (len(values) - 1)
    return [max(0.0, values[-1] + slope * step) for step in range(1, horizon + 1)]
