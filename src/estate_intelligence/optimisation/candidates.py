"""Candidate construction for constrained estate allocation optimisation."""

from __future__ import annotations

import sqlite3
from collections import defaultdict
from typing import Any

from estate_intelligence.optimisation.models import (
    Candidate,
    DemandRow,
    OptimisationConfig,
    RoomCapacity,
)
from estate_intelligence.scenarios.constraints import ROOM_TYPE_ORDER


def build_candidates(
    connection: sqlite3.Connection,
    config: OptimisationConfig,
    *,
    forecast_run_id: str,
    scenario_run_id: str,
) -> tuple[list[Candidate], list[DemandRow], dict[str, RoomCapacity]]:
    """Build deterministic service-month-room candidate assignments."""

    services = {row["service_id"]: row for row in _rows(connection, "curated_services")}
    rooms = _included_rooms(connection)
    buildings = {row["building_id"]: row for row in _rows(connection, "curated_buildings")}
    workforce = _workforce_summary(connection)
    accessibility = _accessibility_summary(connection)
    scenario_compatibility = _scenario_compatibility(connection, scenario_run_id)
    demand_rows = _demand_rows(connection, config, forecast_run_id, services, workforce)
    room_capacity = _room_capacity(config, rooms, buildings)
    candidates = []
    for demand in demand_rows:
        service = services[demand.service_id]
        for room in rooms:
            building = buildings[str(room["building_id"])]
            candidate = _candidate(
                config=config,
                demand=demand,
                service=service,
                room=room,
                building=building,
                workforce=workforce,
                accessibility=accessibility,
                scenario_compatibility=scenario_compatibility,
                capacity=room_capacity[str(room["room_id"])],
            )
            candidates.append(candidate)
    return sorted(candidates, key=lambda item: item.candidate_id), demand_rows, room_capacity


def _candidate(
    *,
    config: OptimisationConfig,
    demand: DemandRow,
    service: dict[str, Any],
    room: dict[str, Any],
    building: dict[str, Any],
    workforce: dict[tuple[str, str], dict[str, float]],
    accessibility: dict[str, dict[str, float]],
    scenario_compatibility: dict[tuple[str, str], str],
    capacity: RoomCapacity,
) -> Candidate:
    service_id = demand.service_id
    room_id = str(room["room_id"])
    target_site_id = str(building["site_id"])
    candidate_id = f"CAND__{service_id}__{demand.period}__{room_id}"
    minimum_type = str(service["minimum_room_type"])
    room_type = str(room["room_type"])
    required_equipment = str(service["specialist_equipment_required"] or "")
    room_equipment = str(room["specialist_equipment"] or "")
    room_type_ok = ROOM_TYPE_ORDER.get(room_type, 0) >= ROOM_TYPE_ORDER.get(minimum_type, 0)
    equipment_ok = not required_equipment or required_equipment in room_equipment
    capacity_ok = int(str(room["capacity"])) >= int(str(service["minimum_capacity"]))
    protected = _bool(room["protected_capacity_flag"])
    protected_effect = "retained_protected" if protected else "none"
    if protected and minimum_type not in {"diagnostic", "specialist"}:
        protected_effect = "protected_capacity_conflict"
    workforce_values = workforce.get((service_id, target_site_id))
    workforce_ok = workforce_values is not None and (
        workforce_values["available"] / workforce_values["planned"]
        if workforce_values["planned"]
        else 0.0
    ) >= _float_config(config.workforce_constraints["minimum_available_fte_ratio"])
    access = accessibility[target_site_id]
    service_distance_limit = float(service["maximum_travel_distance_km"])
    accessibility_ok = (
        access["maximum_distance_km"]
        <= min(
            service_distance_limit,
            config.accessibility_constraints["maximum_travel_distance_km"],
        )
        and access["average_public_transport_score"]
        >= config.accessibility_constraints["minimum_public_transport_score"]
        and access["accessible_transport_coverage"]
        >= config.accessibility_constraints["minimum_accessible_transport_coverage"]
    )
    co_location_ok = True
    if config.co_location_rules["enforce_configured_requirements"] and str(
        service["co_location_requirement"]
    ) not in {"", "none", "standard"}:
        co_location_ok = target_site_id == demand.source_site_id
    confidentiality_ok = True
    requirement = str(service["confidentiality_requirement"])
    if requirement == "strict":
        confidentiality_ok = room_type in config.confidentiality_rules["strict_requires_room_types"]
    elif requirement == "enhanced":
        confidentiality_ok = (
            room_type in config.confidentiality_rules["enhanced_requires_room_types"]
        )
    scenario_status = scenario_compatibility.get((service_id, room_id), "not_observed")
    reasons = []
    if scenario_status.startswith("incompatible") or scenario_status == "missing_equipment":
        reasons.append(f"scenario_{scenario_status}")
    checks = {
        "room_type": room_type_ok,
        "equipment": equipment_ok,
        "capacity": capacity_ok,
        "accessibility": accessibility_ok,
        "workforce": workforce_ok,
        "co_location": co_location_ok,
        "confidentiality": confidentiality_ok,
        "protected_capacity": protected_effect != "protected_capacity_conflict",
    }
    reasons.extend(name for name, ok in checks.items() if not ok)
    status = "excluded" if reasons else "eligible"
    moved = target_site_id != demand.source_site_id
    travel_distance = (
        config.travel_penalty_rules["cross_site_distance_km"]
        if moved
        else config.travel_penalty_rules["home_site_distance_km"]
    )
    return Candidate(
        candidate_id=candidate_id,
        service_id=service_id,
        source_site_id=demand.source_site_id,
        target_site_id=target_site_id,
        target_building_id=str(building["building_id"]),
        target_room_id=room_id,
        period=demand.period,
        planning_demand_hours=round(demand.planning_demand_hours, 4),
        compatible_capacity_hours=round(capacity.allocatable_capacity_hours, 4),
        room_type_compatible=room_type_ok,
        equipment_compatible=equipment_ok,
        capacity_compatible=capacity_ok,
        accessibility_compatible=accessibility_ok,
        workforce_compatible=workforce_ok,
        co_location_compatible=co_location_ok,
        confidentiality_compatible=confidentiality_ok,
        protected_capacity_effect=protected_effect,
        travel_penalty=round(travel_distance, 4),
        relocation_penalty=1.0 if moved else 0.0,
        disruption_penalty=1.0 if moved else 0.0,
        candidate_status=status,
        exclusion_reason=";".join(reasons),
    )


def _demand_rows(
    connection: sqlite3.Connection,
    config: OptimisationConfig,
    forecast_run_id: str,
    services: dict[str, dict[str, Any]],
    workforce: dict[tuple[str, str], dict[str, float]],
) -> list[DemandRow]:
    point_rows = connection.execute(
        """
        SELECT entity_id AS service_id, period, forecast_value
        FROM evidence_forecast_values
        WHERE forecast_run_id = ? AND target = ?
        ORDER BY entity_id, period
        """,
        (forecast_run_id, config.planning_demand_basis.target),
    ).fetchall()
    point = {(row["service_id"], row["period"]): float(row["forecast_value"]) for row in point_rows}
    level = 0.8 if config.planning_demand_basis.interval_basis == "upper_80" else 0.95
    interval = {
        (row["service_id"], row["period"]): float(row["upper_bound"])
        for row in connection.execute(
            """
            SELECT values_table.entity_id AS service_id, intervals.period, intervals.upper_bound
            FROM evidence_forecast_intervals AS intervals
            JOIN evidence_forecast_values AS values_table
              ON values_table.forecast_run_id = intervals.forecast_run_id
             AND values_table.series_id = intervals.series_id
             AND values_table.period = intervals.period
            WHERE values_table.forecast_run_id = ?
              AND values_table.target = ?
              AND intervals.interval_level = ?
            ORDER BY values_table.entity_id, intervals.period
            """,
            (forecast_run_id, config.planning_demand_basis.target, level),
        )
    }
    rows = []
    for service_id, period in sorted(point):
        service = services[service_id]
        source_site_id = _source_site(service_id, workforce)
        rows.append(
            DemandRow(
                service_id=service_id,
                period=period,
                point_demand_hours=round(point[(service_id, period)], 4),
                planning_demand_hours=round(
                    interval.get((service_id, period), point[(service_id, period)]), 4
                ),
                remote_eligible_rate=float(service["remote_eligible_rate"]),
                source_site_id=source_site_id,
            )
        )
    return rows


def _included_rooms(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    return [
        dict(row)
        for row in connection.execute(
            """
            SELECT rooms.*
            FROM curated_rooms AS rooms
            JOIN evidence_analytics_population AS population
              ON population.dataset = 'rooms'
             AND population.record_identifier = rooms.room_id
             AND population.analytical_status = 'included'
            WHERE lower(rooms.active_flag) = 'true'
            ORDER BY rooms.room_id
            """
        )
    ]


def _room_capacity(
    config: OptimisationConfig,
    rooms: list[dict[str, Any]],
    buildings: dict[str, dict[str, Any]],
) -> dict[str, RoomCapacity]:
    available_factor = 52 / 12
    allocatable_share = max(0.0, 1 - config.capacity_buffer - config.contingency_capacity)
    return {
        str(row["room_id"]): RoomCapacity(
            room_id=str(row["room_id"]),
            building_id=str(row["building_id"]),
            site_id=str(buildings[str(row["building_id"])]["site_id"]),
            monthly_capacity_hours=round(
                float(row["available_hours_per_week"]) * available_factor, 4
            ),
            allocatable_capacity_hours=round(
                float(row["available_hours_per_week"]) * available_factor * allocatable_share,
                4,
            ),
            protected_capacity_flag=_bool(row["protected_capacity_flag"]),
            specialist_flag=str(row["room_type"]) in {"diagnostic", "specialist"},
        )
        for row in rooms
    }


def _workforce_summary(
    connection: sqlite3.Connection,
) -> dict[tuple[str, str], dict[str, float]]:
    grouped: dict[tuple[str, str], dict[str, float]] = defaultdict(
        lambda: {"available": 0.0, "planned": 0.0}
    )
    for row in _rows(connection, "curated_workforce"):
        key = (str(row["service_id"]), str(row["site_id"]))
        grouped[key]["available"] += float(row["available_fte"])
        grouped[key]["planned"] += float(row["planned_fte"])
    return dict(grouped)


def _accessibility_summary(connection: sqlite3.Connection) -> dict[str, dict[str, float]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in _rows(connection, "curated_accessibility"):
        grouped[str(row["site_id"])].append(row)
    result = {}
    for site_id, rows in grouped.items():
        result[site_id] = {
            "maximum_distance_km": max(float(row["distance_km"]) for row in rows),
            "average_public_transport_score": sum(
                float(row["public_transport_score"]) for row in rows
            )
            / len(rows),
            "accessible_transport_coverage": sum(
                1 for row in rows if _bool(row["accessible_transport_flag"])
            )
            / len(rows),
        }
    return result


def _scenario_compatibility(
    connection: sqlite3.Connection, scenario_run_id: str
) -> dict[tuple[str, str], str]:
    return {
        (str(row["service_id"]), str(row["room_id"])): str(row["compatibility_status"])
        for row in connection.execute(
            """
            SELECT service_id, room_id, compatibility_status
            FROM evidence_scenario_compatibility
            WHERE scenario_run_id = ?
            ORDER BY service_id, room_id
            """,
            (scenario_run_id,),
        )
    }


def _source_site(service_id: str, workforce: dict[tuple[str, str], dict[str, float]]) -> str:
    matches = [
        (site_id, values["available"])
        for (candidate_service, site_id), values in workforce.items()
        if candidate_service == service_id
    ]
    if not matches:
        return "UNKNOWN"
    return sorted(matches, key=lambda item: (-item[1], item[0]))[0][0]


def _rows(connection: sqlite3.Connection, table: str) -> list[dict[str, Any]]:
    return [dict(row) for row in connection.execute(f"SELECT * FROM {table}")]


def _bool(value: object) -> bool:
    return str(value).lower() == "true"


def _float_config(value: object) -> float:
    if isinstance(value, int | float | str):
        return float(value)
    raise TypeError(f"Expected numeric optimisation configuration value, got {type(value)}")
