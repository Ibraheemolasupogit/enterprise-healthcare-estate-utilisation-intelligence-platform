"""Optimisation result helpers."""

FEASIBLE_STATUSES = {"optimal", "feasible"}


def case_is_feasible(status: str) -> bool:
    return status in FEASIBLE_STATUSES
