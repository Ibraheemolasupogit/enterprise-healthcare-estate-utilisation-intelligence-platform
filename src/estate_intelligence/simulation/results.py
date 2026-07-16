"""Simulation metric helpers."""

from __future__ import annotations

import math
from statistics import mean


def percentile(values: list[float], percentile_value: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * percentile_value
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[int(position)]
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def normal_ci(values: list[float], level: float) -> tuple[float, float]:
    if not values:
        return (0.0, 0.0)
    if len(values) == 1:
        return (values[0], values[0])
    z_value = 1.96 if level >= 0.95 else 1.64
    avg = mean(values)
    variance = sum((value - avg) ** 2 for value in values) / (len(values) - 1)
    margin = z_value * math.sqrt(variance) / math.sqrt(len(values))
    return (avg - margin, avg + margin)


def status_from_thresholds(failures: int, warnings: int = 0) -> str:
    if failures > 0:
        return "fail"
    if warnings > 0:
        return "review_required"
    return "pass"
