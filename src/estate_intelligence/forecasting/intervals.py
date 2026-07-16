"""Deterministic forecast interval helpers."""

from __future__ import annotations


def residual_interval_width(residuals: list[float], level: float) -> float:
    """Return an empirical absolute residual width for an interval level."""

    if not residuals:
        return 1.0
    sorted_residuals = sorted(abs(value) for value in residuals)
    index = min(len(sorted_residuals) - 1, round(level * (len(sorted_residuals) - 1)))
    return sorted_residuals[index]


def build_intervals(
    forecasts: list[float], residuals: list[float], levels: tuple[float, ...]
) -> list[dict[str, float | str | int]]:
    """Build non-negative residual-based intervals for each forecast step."""

    rows: list[dict[str, float | str | int]] = []
    for step, forecast in enumerate(forecasts, start=1):
        for level in levels:
            width = residual_interval_width(residuals, level)
            rows.append(
                {
                    "horizon_step": step,
                    "interval_level": level,
                    "lower_bound": max(0.0, forecast - width),
                    "upper_bound": max(0.0, forecast + width),
                    "interval_method": "empirical_absolute_residual",
                }
            )
    return rows


def coverage(
    actuals: list[float], forecasts: list[float], residuals: list[float], level: float
) -> float | None:
    """Calculate empirical coverage using residual intervals."""

    if not actuals:
        return None
    width = residual_interval_width(residuals, level)
    inside = 0
    for actual, forecast in zip(actuals, forecasts, strict=True):
        if max(0.0, forecast - width) <= actual <= forecast + width:
            inside += 1
    return inside / len(actuals)
