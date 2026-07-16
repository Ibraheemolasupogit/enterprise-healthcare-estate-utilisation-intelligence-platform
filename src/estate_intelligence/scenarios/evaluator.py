"""Deterministic heuristic scenario evaluator."""

from __future__ import annotations

import sqlite3
from collections import defaultdict
from typing import Any

from estate_intelligence.scenarios.capacity import capacity_row
from estate_intelligence.scenarios.comparison import score_dimensions
from estate_intelligence.scenarios.constraints import (
    feasibility_from_constraints,
    room_compatibility,
)
from estate_intelligence.scenarios.models import ScenarioConfig, ScenarioDefinition
from estate_intelligence.scenarios.uncertainty import confidence_status


def evaluate_scenario(
    connection: sqlite3.Connection,
    scenario: ScenarioDefinition,
    scenario_run_id: str,
    config: ScenarioConfig,
) -> dict[str, list[dict[str, Any]]]:
    """Evaluate one configured scenario."""

    rooms = _included_rooms(connection)
    services = _rows(connection, "curated_services")
    buildings = {row["building_id"]: row for row in _rows(connection, "curated_buildings")}
    costs = {row["building_id"]: row for row in _rows(connection, "evidence_unit_cost_metrics")}
    forecast = _forecast_demand(connection, config)
    total_point = sum(row["point"] for row in forecast.values())
    total_interval = sum(row["upper"] for row in forecast.values())
    planning = total_interval if config.forecast_interval_basis != "point" else total_point
    total_available = sum(
        float(row["available_hours_per_week"]) * 52 / 12 * config.analysis_horizon_months
        for row in rooms
    )
    specialist = [row for row in rooms if str(row["room_type"]) in {"diagnostic", "specialist"}]
    deactivated = _deactivated_rooms(connection, rooms, scenario.scenario_type, config)
    retained = [
        row for row in rooms if row["room_id"] not in {item["room_id"] for item in deactivated}
    ]
    compatible_hours = sum(
        float(row["available_hours_per_week"]) * 52 / 12 * config.analysis_horizon_months
        for row in retained
    )
    if scenario.scenario_type == "hybrid_redesign":
        planning *= 0.93
    if scenario.scenario_type == "site_consolidation":
        planning *= 1.03
    capacity = capacity_row(
        point_demand=total_point,
        interval_demand=total_interval,
        planning_demand=planning,
        available_hours=total_available,
        compatible_hours=compatible_hours,
        retained_rooms=len(retained),
        deactivated_rooms=len(deactivated),
        protected_rooms=len([row for row in retained if _bool(row["protected_capacity_flag"])]),
        specialist_rooms=len([row for row in retained if row in specialist]),
        contingency_rate=config.contingency_capacity,
    )
    room_actions = _room_actions(scenario_run_id, scenario.scenario_id, rooms, deactivated)
    compatibility = _compatibility_rows(scenario_run_id, scenario.scenario_id, services, retained)
    workforce = _workforce_rows(connection, scenario_run_id, scenario.scenario_id, config)
    accessibility = _accessibility_rows(connection, scenario_run_id, scenario.scenario_id, config)
    service_moves = _service_moves(scenario_run_id, scenario, forecast, buildings)
    recurring = _scenario_cost(costs, retained)
    baseline_cost = _scenario_cost(costs, rooms)
    cost_difference = recurring - baseline_cost
    burden = min(1.0, (len(deactivated) * 0.01) + (len(service_moves) * 0.05))
    constraints = _constraint_rows(
        scenario_run_id,
        scenario.scenario_id,
        capacity,
        room_actions,
        workforce,
        accessibility,
        config,
    )
    feasibility = feasibility_from_constraints(constraints)
    manual_reviews = sum(1 for row in constraints if row["result_status"] == "warning")
    confidence = confidence_status(manual_reviews, float(capacity["capacity_headroom"]) / planning)
    risk_rows = _risk_rows(scenario_run_id, scenario.scenario_id, confidence, constraints, capacity)
    score_rows = score_dimensions(
        capacity_margin=float(capacity["capacity_headroom"]) / planning,
        workforce_ok=all(row["status"] != "infeasible" for row in workforce),
        accessibility_ok=all(row["accessibility_status"] != "infeasible" for row in accessibility),
        cost_difference=cost_difference,
        burden=burden,
        confidence=confidence,
        risk_count=len([row for row in risk_rows if row["risk_level"] != "low"]),
        weights=config.scoring_weights,
    )
    comparison_score = (
        0.0
        if feasibility == "infeasible"
        else sum(float(row["weighted_score"]) for row in score_rows)
    )
    cost_rows = [
        {
            "scenario_run_id": scenario_run_id,
            "scenario_id": scenario.scenario_id,
            "baseline_recurring_cost": round(baseline_cost, 4),
            "scenario_recurring_cost": round(recurring, 4),
            "descriptive_recurring_cost_difference": round(cost_difference, 4),
            "indicative_transition_cost_exposure": round(
                abs(cost_difference)
                * _float_config(config.cost_components["transition_exposure_factor"]),
                4,
            ),
            "planned_capital_cost_exposure": round(
                abs(cost_difference)
                * _float_config(config.cost_components["planned_capital_exposure_factor"]),
                4,
            ),
            "exit_cost_exposure": round(
                abs(cost_difference)
                * _float_config(config.cost_components["exit_exposure_factor"]),
                4,
            ),
            "relocation_cost_exposure": round(
                abs(cost_difference)
                * _float_config(config.cost_components["relocation_exposure_factor"]),
                4,
            ),
            "cost_statement": "descriptive recurring cost difference; not an audited saving",
        }
    ]
    return {
        "candidates": _candidate_rows(scenario_run_id, scenario.scenario_id, deactivated),
        "room_actions": room_actions,
        "service_moves": service_moves,
        "capacity": [
            {
                "scenario_run_id": scenario_run_id,
                "scenario_id": scenario.scenario_id,
                "grain": "estate",
                "entity_id": "estate",
                **capacity,
            }
        ],
        "compatibility": compatibility,
        "workforce": workforce,
        "accessibility": accessibility,
        "costs": cost_rows,
        "constraints": constraints,
        "risks": risk_rows,
        "scores": [
            {"scenario_run_id": scenario_run_id, "scenario_id": scenario.scenario_id, **row}
            for row in score_rows
        ],
        "comparison": [
            {
                "scenario_run_id": scenario_run_id,
                "scenario_id": scenario.scenario_id,
                "feasibility_status": feasibility,
                "comparison_score": round(comparison_score, 4),
                "confidence_status": confidence,
                "rooms_retained": int(capacity["rooms_retained"]),
                "rooms_deactivated": int(capacity["rooms_deactivated"]),
                "buildings_affected": len({row["building_id"] for row in deactivated}),
                "services_moved": len(service_moves),
                "planning_demand_room_hours": float(capacity["planning_demand_room_hours"]),
                "compatible_capacity_room_hours": float(
                    capacity["compatible_available_room_hours"]
                ),
                "capacity_headroom": float(capacity["capacity_headroom"]),
                "unallocated_demand": float(capacity["unallocated_demand"]),
                "protected_capacity_retained": int(capacity["protected_rooms_retained"]),
                "comparison_statement": (
                    "comparison score only; not an implementation recommendation"
                ),
            }
        ],
    }


def _included_rooms(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    return [
        dict(row)
        for row in connection.execute(
            """
            SELECT rooms.*
            FROM curated_rooms AS rooms
            JOIN evidence_analytics_population AS population
              ON population.dataset='rooms'
             AND population.record_identifier=rooms.room_id
             AND population.analytical_status='included'
            ORDER BY rooms.room_id
            """
        )
    ]


def _forecast_demand(
    connection: sqlite3.Connection, config: ScenarioConfig
) -> dict[str, dict[str, float]]:
    point_rows = connection.execute(
        """
        SELECT series_id, SUM(forecast_value) AS demand
        FROM evidence_forecast_values
        WHERE target = ?
        GROUP BY series_id
        ORDER BY series_id
        """,
        (config.forecast_demand_basis,),
    ).fetchall()
    demand = {
        row["series_id"]: {"point": float(row["demand"]), "upper": float(row["demand"])}
        for row in point_rows
    }
    level = 0.8 if config.forecast_interval_basis == "upper_80" else 0.95
    if config.forecast_interval_basis != "point":
        for row in connection.execute(
            """
            SELECT intervals.series_id, SUM(intervals.upper_bound) AS demand
            FROM evidence_forecast_intervals AS intervals
            JOIN evidence_forecast_values AS forecast_values
              ON forecast_values.forecast_run_id=intervals.forecast_run_id
             AND forecast_values.series_id=intervals.series_id
             AND forecast_values.period=intervals.period
            WHERE forecast_values.target = ? AND intervals.interval_level = ?
            GROUP BY intervals.series_id
            ORDER BY intervals.series_id
            """,
            (config.forecast_demand_basis, level),
        ):
            demand[row["series_id"]]["upper"] = float(row["demand"])
    return demand


def _deactivated_rooms(
    connection: sqlite3.Connection,
    rooms: list[dict[str, Any]],
    scenario_type: str,
    config: ScenarioConfig,
) -> list[dict[str, Any]]:
    if scenario_type == "baseline":
        return []
    candidates = [
        dict(row)
        for row in connection.execute(
            """
            SELECT flags.room_id, util.building_id, util.actual_utilisation
            FROM evidence_underutilisation_flags AS flags
            JOIN evidence_room_utilisation AS util ON util.room_id = flags.room_id
            WHERE flags.persistent_flag=1 AND flags.protected_capacity_flag=0
            ORDER BY util.actual_utilisation, flags.room_id
            """
        )
    ]
    room_map = {row["room_id"]: row for row in rooms}
    limit = 4 if scenario_type == "light_consolidation" else 6
    if scenario_type == "site_consolidation":
        limit = 3
    selected = []
    for candidate in candidates:
        room = room_map.get(candidate["room_id"])
        if room is None:
            continue
        if (
            str(room["room_type"]) in {"diagnostic", "specialist"}
            and not config.specialist_capacity_policy["allow_specialist_release"]
        ):
            continue
        selected.append(room)
        if len(selected) >= limit:
            break
    return selected


def _room_actions(
    scenario_run_id: str,
    scenario_id: str,
    rooms: list[dict[str, Any]],
    deactivated: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    deactivated_ids = {row["room_id"] for row in deactivated}
    return [
        {
            "scenario_run_id": scenario_run_id,
            "scenario_id": scenario_id,
            "room_id": row["room_id"],
            "building_id": row["building_id"],
            "action": "deactivate_candidate" if row["room_id"] in deactivated_ids else "retain",
            "reason": "persistent low utilisation candidate"
            if row["room_id"] in deactivated_ids
            else "retained by scenario rule",
            "protected_capacity_flag": 1 if _bool(row["protected_capacity_flag"]) else 0,
            "specialist_flag": 1 if str(row["room_type"]) in {"diagnostic", "specialist"} else 0,
        }
        for row in rooms
    ]


def _candidate_rows(
    scenario_run_id: str, scenario_id: str, deactivated: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    return [
        {
            "scenario_run_id": scenario_run_id,
            "scenario_id": scenario_id,
            "candidate_type": "room_release",
            "entity_id": row["room_id"],
            "rank_value": float(index),
            "selected_flag": 1,
            "reason": "selected by stable low-utilisation heuristic",
        }
        for index, row in enumerate(deactivated, start=1)
    ]


def _compatibility_rows(
    scenario_run_id: str,
    scenario_id: str,
    services: list[dict[str, Any]],
    rooms: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for service in services:
        for room in rooms[:12]:
            status, reason = room_compatibility(service, room)
            rows.append(
                {
                    "scenario_run_id": scenario_run_id,
                    "scenario_id": scenario_id,
                    "service_id": service["service_id"],
                    "room_id": room["room_id"],
                    "compatibility_status": status,
                    "reason": reason,
                }
            )
    return rows


def _workforce_rows(
    connection: sqlite3.Connection, scenario_run_id: str, scenario_id: str, config: ScenarioConfig
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], dict[str, float]] = defaultdict(
        lambda: {"available": 0.0, "planned": 0.0, "absence": 0.0, "vacancy": 0.0, "count": 0.0}
    )
    for row in _rows(connection, "curated_workforce"):
        key = (str(row["service_id"]), str(row["site_id"]))
        grouped[key]["available"] += float(row["available_fte"])
        grouped[key]["planned"] += float(row["planned_fte"])
        grouped[key]["absence"] += float(row["absence_rate"])
        grouped[key]["vacancy"] += float(row["vacancy_rate"])
        grouped[key]["count"] += 1
    rows = []
    for (service_id, site_id), values in sorted(grouped.items()):
        ratio = values["available"] / values["planned"] if values["planned"] else 0.0
        warning = None
        status = "feasible"
        if ratio < config.workforce_constraints["minimum_available_fte_ratio"]:
            status = "manual_review"
            warning = "available FTE ratio below configured threshold"
        rows.append(
            {
                "scenario_run_id": scenario_run_id,
                "scenario_id": scenario_id,
                "service_id": service_id,
                "site_id": site_id,
                "available_fte": round(values["available"], 4),
                "planned_fte": round(values["planned"], 4),
                "availability_ratio": round(ratio, 4),
                "status": status,
                "warning": warning,
            }
        )
    return rows


def _accessibility_rows(
    connection: sqlite3.Connection, scenario_run_id: str, scenario_id: str, config: ScenarioConfig
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in _rows(connection, "curated_accessibility"):
        grouped[str(row["site_id"])].append(row)
    rows = []
    for site_id, values in sorted(grouped.items()):
        distances = [float(row["distance_km"]) for row in values]
        minutes = [float(row["estimated_travel_minutes"]) for row in values]
        scores = [float(row["public_transport_score"]) for row in values]
        coverage = sum(1 for row in values if _bool(row["accessible_transport_flag"])) / len(values)
        max_distance = max(distances)
        status = (
            "feasible"
            if max_distance <= config.accessibility_constraints["maximum_travel_distance_km"]
            else "manual_review"
        )
        rows.append(
            {
                "scenario_run_id": scenario_run_id,
                "scenario_id": scenario_id,
                "site_id": site_id,
                "origin_areas": len(values),
                "average_distance_km": round(sum(distances) / len(distances), 4),
                "maximum_distance_km": round(max_distance, 4),
                "average_travel_minutes": round(sum(minutes) / len(minutes), 4),
                "average_public_transport_score": round(sum(scores) / len(scores), 4),
                "accessible_transport_coverage": round(coverage, 4),
                "accessibility_status": status,
                "warning": None
                if status == "feasible"
                else "maximum synthetic travel distance exceeded",
            }
        )
    return rows


def _service_moves(
    scenario_run_id: str,
    scenario: ScenarioDefinition,
    forecast: dict[str, dict[str, float]],
    buildings: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    if scenario.scenario_type in {"baseline", "light_consolidation"}:
        return []
    site_ids = sorted({str(row["site_id"]) for row in buildings.values()})
    target_site = site_ids[-1]
    rows = []
    for index, (series_id, demand) in enumerate(sorted(forecast.items()), start=1):
        service_id = series_id.split("|")[-1] if "|" in series_id else f"SVC-{index:03d}"
        if service_id == "estate":
            service_id = f"SVC-{index:03d}"
        rows.append(
            {
                "scenario_run_id": scenario_run_id,
                "scenario_id": scenario.scenario_id,
                "service_id": service_id,
                "from_site_id": site_ids[0],
                "to_site_id": target_site,
                "planning_demand_room_hours": round(demand["upper"], 4),
                "status": "manual_review",
                "reason": "heuristic relocation candidate; not a recommendation",
            }
        )
        if index >= 3:
            break
    return rows


def _scenario_cost(costs: dict[str, dict[str, Any]], rooms: list[dict[str, Any]]) -> float:
    buildings = {row["building_id"] for row in rooms}
    return sum(
        float(costs[building_id]["annual_operating_cost"])
        for building_id in buildings
        if building_id in costs
    )


def _constraint_rows(
    scenario_run_id: str,
    scenario_id: str,
    capacity: dict[str, Any],
    room_actions: list[dict[str, Any]],
    workforce: list[dict[str, Any]],
    accessibility: list[dict[str, Any]],
    config: ScenarioConfig,
) -> list[dict[str, Any]]:
    removed_protected = any(
        row["action"] != "retain" and row["protected_capacity_flag"] for row in room_actions
    )
    rows = [
        _constraint(
            scenario_run_id,
            scenario_id,
            "capacity",
            "planning_demand_within_capacity",
            float(capacity["capacity_shortfall"]) == 0.0,
            True,
            "planning demand must fit compatible capacity",
        ),
        _constraint(
            scenario_run_id,
            scenario_id,
            "capacity",
            "contingency_capacity_available",
            float(capacity["contingency_headroom"]) >= 0.0,
            True,
            "configured contingency must remain available",
        ),
        _constraint(
            scenario_run_id,
            scenario_id,
            "specialist",
            "protected_capacity_retained",
            not removed_protected,
            True,
            "protected specialist rooms must be retained",
        ),
        _constraint(
            scenario_run_id,
            scenario_id,
            "workforce",
            "workforce_feasible",
            all(row["status"] != "manual_review" for row in workforce),
            False,
            "workforce warnings require review",
        ),
        _constraint(
            scenario_run_id,
            scenario_id,
            "accessibility",
            "synthetic_travel_within_threshold",
            all(row["accessibility_status"] == "feasible" for row in accessibility),
            False,
            "accessibility warnings require review",
        ),
    ]
    if float(capacity["utilisation_after_scenario"]) > 1 - config.capacity_buffer:
        rows.append(
            _constraint(
                scenario_run_id,
                scenario_id,
                "risk",
                "capacity_buffer_warning",
                False,
                False,
                "post-scenario utilisation approaches configured buffer",
            )
        )
    return rows


def _constraint(
    scenario_run_id: str,
    scenario_id: str,
    category: str,
    name: str,
    passed: bool,
    critical: bool,
    detail: str,
) -> dict[str, Any]:
    return {
        "scenario_run_id": scenario_run_id,
        "scenario_id": scenario_id,
        "constraint_category": category,
        "constraint_name": name,
        "result_status": "pass" if passed else ("fail" if critical else "warning"),
        "critical_flag": 1 if critical else 0,
        "detail": detail,
    }


def _risk_rows(
    scenario_run_id: str,
    scenario_id: str,
    confidence: str,
    constraints: list[dict[str, Any]],
    capacity: dict[str, Any],
) -> list[dict[str, Any]]:
    warning_count = sum(1 for row in constraints if row["result_status"] == "warning")
    return [
        {
            "scenario_run_id": scenario_run_id,
            "scenario_id": scenario_id,
            "risk_category": "forecast_uncertainty",
            "risk_level": "moderate" if float(capacity["contingency_headroom"]) < 0 else "low",
            "confidence_status": confidence,
            "detail": "upper interval demand retained in planning basis",
        },
        {
            "scenario_run_id": scenario_run_id,
            "scenario_id": scenario_id,
            "risk_category": "manual_review_dependencies",
            "risk_level": "moderate" if warning_count else "low",
            "confidence_status": confidence,
            "detail": f"{warning_count} warning constraints require local review",
        },
    ]


def _rows(connection: sqlite3.Connection, table: str) -> list[dict[str, Any]]:
    return [dict(row) for row in connection.execute(f"SELECT * FROM {table}")]


def _bool(value: object) -> bool:
    return str(value).lower() == "true"


def _float_config(value: object) -> float:
    if isinstance(value, int | float | str):
        return float(value)
    raise TypeError(f"Expected numeric scenario configuration value, got {type(value)}")
