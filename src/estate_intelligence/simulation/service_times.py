"""Service-time generation for synthetic operational simulation."""

from __future__ import annotations

import random

from estate_intelligence.simulation.models import ServiceInput, SimulationConfig


def sampled_duration(
    config: SimulationConfig,
    service: ServiceInput,
    duration_multiplier: float,
    rng: random.Random,
) -> float:
    distribution = config.service_time_distributions
    overrides = distribution.get("service_overrides", {})
    room_type = service.minimum_room_type
    params: dict[str, object] = {}
    if isinstance(overrides, dict) and isinstance(overrides.get(room_type), dict):
        params = dict(overrides[room_type])
    default_minimum = _float_value(distribution["default_min_minutes"])
    default_mode = max(
        _float_value(distribution["default_mode_minutes"]),
        service.average_duration_minutes,
    )
    default_maximum = _float_value(distribution["default_max_minutes"])
    minimum = _float_value(params.get("min_minutes", default_minimum))
    mode = _float_value(params.get("mode_minutes", default_mode))
    maximum = _float_value(params.get("max_minutes", default_maximum))
    cap = _float_value(distribution["cap_minutes"])
    duration = rng.triangular(minimum, maximum, mode) * duration_multiplier
    return max(1.0, min(duration, cap))


def _float_value(value: object) -> float:
    if isinstance(value, int | float | str):
        return float(value)
    raise TypeError(f"Expected numeric service-time value, got {type(value)}")
