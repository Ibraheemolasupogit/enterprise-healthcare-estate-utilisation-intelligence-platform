"""Utilisation scoring helpers."""

from __future__ import annotations


def readiness_status(effective_utilisation: float) -> str:
    """Map estate-level effective utilisation to an analytical-readiness label."""

    if effective_utilisation >= 0.5:
        return "ready_with_caveats"
    return "review_required"


def persistent_underutilisation_flag(
    months_below_threshold: int,
    observation_count: int,
    minimum_below: int,
    minimum_observations: int,
) -> bool:
    """Return whether a room meets the configured persistence rule."""

    return observation_count >= minimum_observations and months_below_threshold >= minimum_below
