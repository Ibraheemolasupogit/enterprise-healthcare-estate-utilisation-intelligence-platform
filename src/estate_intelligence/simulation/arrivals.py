"""Arrival construction from forecast and allocation evidence."""

from __future__ import annotations

import math
import random
from collections.abc import Callable

from estate_intelligence.simulation.models import (
    AllocationInput,
    Arrival,
    ServiceInput,
    SimulationConfig,
)


def build_arrivals(
    *,
    config: SimulationConfig,
    allocations: list[AllocationInput],
    services: dict[str, ServiceInput],
    demand_multiplier: float,
    duration_multiplier: float,
    lateness_rng: random.Random,
    cancellation_rng: random.Random,
    no_show_rng: random.Random,
    duration_rng: random.Random,
    duration_fn: Callable[[SimulationConfig, ServiceInput, float, random.Random], float],
) -> list[Arrival]:
    """Convert monthly room-hour allocations into representative scheduled contacts."""

    arrivals: list[Arrival] = []
    sequence = 0
    horizon = config.simulation_horizon
    month_count = max(1, len({allocation.period for allocation in allocations}))
    scale = horizon / (month_count * config.working_days_per_month)
    cancellation_probability = _probability(config.cancellation_rules)
    no_show_probability = _probability(config.no_show_rules)
    late_min = float(config.arrival_process["lateness_minutes_min"])
    late_mode = float(config.arrival_process["lateness_minutes_mode"])
    late_max = float(config.arrival_process["lateness_minutes_max"])
    day_minutes = 24 * 60
    for allocation in sorted(
        allocations, key=lambda item: (item.service_id, item.period, item.room_id)
    ):
        service = services[allocation.service_id]
        expected_minutes = allocation.allocated_hours * 60 * demand_multiplier * scale
        base_duration = service.average_duration_minutes * duration_multiplier
        count = max(0, round(expected_minutes / max(base_duration, 1.0)))
        if expected_minutes > 0 and count == 0:
            count = 1
        for contact in range(count):
            day = contact % horizon
            slot = contact // horizon
            planned = day * day_minutes + 8 * 60 + (slot * max(base_duration, 15.0))
            lateness = lateness_rng.triangular(late_min, late_max, late_mode)
            sequence += 1
            duration = float(duration_fn(config, service, duration_multiplier, duration_rng))
            arrivals.append(
                Arrival(
                    sequence=sequence,
                    service_id=allocation.service_id,
                    room_id=allocation.room_id,
                    arrival_minute=max(0.0, planned + lateness),
                    duration_minutes=duration,
                    cancelled=cancellation_rng.random() < cancellation_probability,
                    no_show=no_show_rng.random() < no_show_probability,
                )
            )
    return sorted(arrivals, key=lambda item: (item.arrival_minute, item.sequence))


def _probability(rules: dict[str, bool | float]) -> float:
    if not bool(rules.get("enabled", False)):
        return 0.0
    return min(max(float(rules.get("probability", 0.0)), 0.0), 1.0)


def reconciled_contact_count(hours: float, duration_minutes: float) -> int:
    return max(0, math.floor((hours * 60 / max(duration_minutes, 1.0)) + 0.5))
