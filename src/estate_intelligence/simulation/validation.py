"""Validation helpers for simulation evidence."""

from __future__ import annotations


def threshold_status(
    threshold_name: str,
    observed_value: float,
    threshold_value: float,
) -> str:
    minimum_thresholds = {
        "minimum_completion_rate",
        "minimum_contingency_remaining",
    }
    if threshold_name in minimum_thresholds:
        return "pass" if observed_value >= threshold_value else "fail"
    return "pass" if observed_value <= threshold_value else "fail"
