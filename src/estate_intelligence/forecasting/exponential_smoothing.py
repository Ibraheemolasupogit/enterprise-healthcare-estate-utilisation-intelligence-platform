"""Small deterministic exponential-smoothing models."""

from __future__ import annotations


def simple_exponential_smoothing(
    values: list[float], horizon: int, alpha: float = 0.4
) -> list[float]:
    """Simple exponential smoothing with fixed configured alpha."""

    if not values:
        return [0.0 for _ in range(horizon)]
    level = values[0]
    for value in values[1:]:
        level = alpha * value + (1 - alpha) * level
    return [max(0.0, level) for _ in range(horizon)]


def holt_linear(
    values: list[float], horizon: int, alpha: float = 0.5, beta: float = 0.2
) -> list[float]:
    """Holt linear trend smoothing with fixed configured parameters."""

    if len(values) < 2:
        return simple_exponential_smoothing(values, horizon, alpha=alpha)
    level = values[0]
    trend = values[1] - values[0]
    for value in values[1:]:
        previous_level = level
        level = alpha * value + (1 - alpha) * (level + trend)
        trend = beta * (level - previous_level) + (1 - beta) * trend
    return [max(0.0, level + step * trend) for step in range(1, horizon + 1)]


def holt_winters_additive(
    values: list[float],
    horizon: int,
    seasonal_period: int,
    alpha: float = 0.4,
    beta: float = 0.1,
    gamma: float = 0.1,
) -> list[float]:
    """Additive Holt-Winters with deterministic fixed smoothing parameters."""

    if len(values) < seasonal_period * 2:
        raise ValueError("Holt-Winters requires at least two seasonal cycles")
    first = values[:seasonal_period]
    second = values[seasonal_period : seasonal_period * 2]
    level = sum(first) / seasonal_period
    trend = (sum(second) / seasonal_period - level) / seasonal_period
    seasonals = [value - level for value in first]
    for index, value in enumerate(values):
        season_index = index % seasonal_period
        previous_level = level
        seasonal = seasonals[season_index]
        level = alpha * (value - seasonal) + (1 - alpha) * (level + trend)
        trend = beta * (level - previous_level) + (1 - beta) * trend
        seasonals[season_index] = gamma * (value - level) + (1 - gamma) * seasonal
    forecasts = []
    for step in range(1, horizon + 1):
        seasonal = seasonals[(len(values) + step - 1) % seasonal_period]
        forecasts.append(max(0.0, level + step * trend + seasonal))
    return forecasts
