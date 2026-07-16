"""Capacity calculations for deterministic scenarios."""

from __future__ import annotations


def capacity_row(
    *,
    point_demand: float,
    interval_demand: float,
    planning_demand: float,
    available_hours: float,
    compatible_hours: float,
    retained_rooms: int,
    deactivated_rooms: int,
    protected_rooms: int,
    specialist_rooms: int,
    contingency_rate: float,
) -> dict[str, float | int]:
    """Return a bounded capacity evidence row."""

    headroom = compatible_hours - planning_demand
    contingency = compatible_hours - planning_demand * (1 + contingency_rate)
    return {
        "point_demand_room_hours": round(point_demand, 4),
        "interval_demand_room_hours": round(interval_demand, 4),
        "planning_demand_room_hours": round(planning_demand, 4),
        "available_room_hours": round(available_hours, 4),
        "compatible_available_room_hours": round(compatible_hours, 4),
        "capacity_headroom": round(headroom, 4),
        "contingency_headroom": round(contingency, 4),
        "capacity_shortfall": round(max(0.0, -headroom), 4),
        "utilisation_after_scenario": round(planning_demand / compatible_hours, 4)
        if compatible_hours
        else 0.0,
        "rooms_retained": retained_rooms,
        "rooms_deactivated": deactivated_rooms,
        "protected_rooms_retained": protected_rooms,
        "specialist_rooms_retained": specialist_rooms,
        "unallocated_demand": round(max(0.0, -headroom), 4),
    }
