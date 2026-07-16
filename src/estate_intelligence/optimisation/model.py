"""MILP model construction and evidence extraction."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

import numpy as np

from estate_intelligence.optimisation.constraints import (
    building_activation_constraint,
    demand_constraint,
    face_to_face_floor_constraint,
    move_activation_constraint,
    protected_room_constraint,
    remote_limit_constraint,
    room_activation_constraint,
    room_capacity_constraint,
)
from estate_intelligence.optimisation.models import (
    Candidate,
    DemandRow,
    OptimisationCase,
    OptimisationConfig,
    OptimisationEvidence,
    RoomCapacity,
    SolverCaseResult,
)
from estate_intelligence.optimisation.objective import OBJECTIVE_UNITS
from estate_intelligence.optimisation.solver import (
    map_solver_status,
    native_status_name,
    scipy_milp_components,
    solver_version,
)


def solve_case(
    *,
    optimisation_run_id: str,
    case: OptimisationCase,
    config: OptimisationConfig,
    candidates: list[Candidate],
    demand_rows: list[DemandRow],
    rooms: dict[str, RoomCapacity],
    building_sites: dict[str, str],
    room_recurring_costs: dict[str, float],
) -> OptimisationEvidence:
    """Build, solve and translate one optimisation case."""

    milp, linear_constraint, bounds_type, _ = scipy_milp_components()
    eligible = [
        candidate
        for candidate in candidates
        if candidate.is_eligible
        and (case.allow_site_movement or candidate.source_site_id == candidate.target_site_id)
    ]
    index = _variable_index(case, eligible, demand_rows, rooms, building_sites)
    objective = _objective_vector(config, eligible, demand_rows, rooms, room_recurring_costs, index)
    constraints, evidence_specs = _constraints(config, case, eligible, demand_rows, rooms, index)
    lower, upper, integrality = _bounds(case, config, demand_rows, rooms, building_sites, index)
    result = milp(
        c=np.array(objective),
        integrality=np.array(integrality),
        bounds=bounds_type(np.array(lower), np.array(upper)),
        constraints=linear_constraint(
            np.array([row[0] for row in constraints]),
            np.array([row[1] for row in constraints]),
            np.array([row[2] for row in constraints]),
        ),
        options={
            "time_limit": config.solver_time_limit_seconds,
            "mip_rel_gap": config.solver_mip_gap,
            "disp": False,
        },
    )
    solution = (
        np.array(result.x, dtype=float)
        if getattr(result, "x", None) is not None
        else np.zeros(len(objective), dtype=float)
    )
    native_status = native_status_name(int(result.status))
    allocations = _allocation_rows(
        optimisation_run_id, case.case_id, eligible, demand_rows, index, solution
    )
    variables = _variable_rows(optimisation_run_id, case.case_id, index, lower, upper, solution)
    room_status = _room_status_rows(optimisation_run_id, case.case_id, rooms, index, solution)
    building_status = _building_status_rows(
        optimisation_run_id, case.case_id, building_sites, rooms, index, solution
    )
    service_moves = _service_move_rows(optimisation_run_id, case.case_id, eligible, index, solution)
    constraint_rows, binding = _constraint_rows(
        optimisation_run_id, case.case_id, evidence_specs, constraints, solution
    )
    components = _objective_component_rows(
        optimisation_run_id,
        case.case_id,
        config,
        eligible,
        demand_rows,
        rooms,
        room_recurring_costs,
        index,
        solution,
    )
    case_result = _case_result(
        case_id=case.case_id,
        native_status=native_status,
        objective_value=float(result.fun) if result.fun is not None else 0.0,
        demand_rows=demand_rows,
        allocations=allocations,
        room_status=room_status,
        building_status=building_status,
        service_moves=service_moves,
    )
    solver_results = [
        {
            "optimisation_run_id": optimisation_run_id,
            "case_id": case.case_id,
            "solver_name": "SciPy HiGHS MILP",
            "solver_version": solver_version(),
            "solver_status": native_status,
            "mapped_status": case_result.solver_status,
            "objective_value": round(case_result.objective_value, 4),
            "objective_gap": case_result.objective_gap,
            "unmet_demand_hours": round(case_result.unmet_demand_hours, 4),
            "allocated_demand_hours": round(case_result.allocated_demand_hours, 4),
            "remote_demand_hours": round(case_result.remote_demand_hours, 4),
            "solve_diagnostics": str(result.message),
        }
    ]
    infeasibility = _infeasibility_rows(
        optimisation_run_id, case.case_id, case_result, demand_rows, eligible, rooms, candidates
    )
    comparison = [
        {
            "optimisation_run_id": optimisation_run_id,
            "case_id": case.case_id,
            "solver_status": case_result.solver_status,
            "objective_value": round(case_result.objective_value, 4),
            "planning_demand_hours": round(
                sum(row.planning_demand_hours for row in demand_rows), 4
            ),
            "allocated_demand_hours": round(case_result.allocated_demand_hours, 4),
            "unmet_demand_hours": round(case_result.unmet_demand_hours, 4),
            "active_rooms": case_result.active_rooms,
            "inactive_rooms": case_result.inactive_rooms,
            "active_buildings": case_result.active_buildings,
            "potentially_releasable_buildings": case_result.potentially_releasable_buildings,
            "services_moved": case_result.services_moved,
            "remote_demand_hours": round(case_result.remote_demand_hours, 4),
            "comparison_statement": (
                "mathematical allocation evidence only; not an implementation recommendation"
            ),
        }
    ]
    return OptimisationEvidence(
        candidates=[],
        variables=variables,
        allocations=allocations,
        room_status=room_status,
        building_status=building_status,
        service_moves=service_moves,
        constraints=constraint_rows,
        binding_constraints=binding,
        objective_components=components,
        solver_results=solver_results,
        infeasibility=infeasibility,
        comparison=comparison,
    )


def _variable_index(
    case: OptimisationCase,
    eligible: list[Candidate],
    demand_rows: list[DemandRow],
    rooms: dict[str, RoomCapacity],
    building_sites: dict[str, str],
) -> dict[str, dict[Any, int]]:
    index: dict[str, dict[Any, int]] = {
        "x": {},
        "y": {},
        "z": {},
        "u": {},
        "r": {},
        "m": {},
    }
    offset = 0
    for candidate in sorted(eligible, key=lambda item: item.candidate_id):
        index["x"][candidate.candidate_id] = offset
        offset += 1
    for room_id in sorted(rooms):
        index["y"][room_id] = offset
        offset += 1
    for building_id in sorted(building_sites):
        index["z"][building_id] = offset
        offset += 1
    for demand in demand_rows:
        demand_key = (demand.service_id, demand.period)
        index["u"][demand_key] = offset
        offset += 1
    for demand in demand_rows:
        demand_key = (demand.service_id, demand.period)
        index["r"][demand_key] = offset
        offset += 1
    move_keys = sorted(
        {
            (candidate.service_id, candidate.source_site_id, candidate.target_site_id)
            for candidate in eligible
            if candidate.source_site_id != candidate.target_site_id and case.allow_site_movement
        }
    )
    for move_key in move_keys:
        index["m"][move_key] = offset
        offset += 1
    return index


def _objective_vector(
    config: OptimisationConfig,
    eligible: list[Candidate],
    demand_rows: list[DemandRow],
    rooms: dict[str, RoomCapacity],
    room_recurring_costs: dict[str, float],
    index: dict[str, dict[Any, int]],
) -> list[float]:
    size = _variable_count(index)
    coeffs = [0.0] * size
    cost = config.cost_coefficients
    weights = config.objective_weights
    for candidate in eligible:
        idx = index["x"][candidate.candidate_id]
        coeffs[idx] += (
            weights["travel_penalty"]
            * cost["travel_penalty_per_km_hour"]
            * candidate.travel_penalty
        )
        coeffs[idx] += (
            weights["disruption_penalty"]
            * cost["disruption_penalty_per_moved_hour"]
            * candidate.disruption_penalty
        )
        coeffs[idx] -= (
            weights["underutilisation_penalty"] * cost["underutilisation_penalty_per_unused_hour"]
        )
        coeffs[idx] += cost["deterministic_tie_breaker"] * (idx + 1)
    for room_id, room in rooms.items():
        idx = index["y"][room_id]
        coeffs[idx] += weights["retained_recurring_estate_cost"] * room_recurring_costs[room_id]
        coeffs[idx] += weights["room_activation_cost"] * cost["room_activation_cost_per_room"]
        coeffs[idx] += (
            weights["underutilisation_penalty"]
            * cost["underutilisation_penalty_per_unused_hour"]
            * room.allocatable_capacity_hours
        )
    for demand in demand_rows:
        key = (demand.service_id, demand.period)
        coeffs[index["u"][key]] += (
            weights["unmet_demand_penalty"] * cost["unmet_demand_penalty_per_hour"]
        )
    for key, idx in index["m"].items():
        del key
        coeffs[idx] += weights["service_relocation_cost"] * cost["service_relocation_cost_per_move"]
    return coeffs


def _bounds(
    case: OptimisationCase,
    config: OptimisationConfig,
    demand_rows: list[DemandRow],
    rooms: dict[str, RoomCapacity],
    building_sites: dict[str, str],
    index: dict[str, dict[Any, int]],
) -> tuple[list[float], list[float], list[int]]:
    size = _variable_count(index)
    lower = [0.0] * size
    upper = [np.inf] * size
    integrality = [0] * size
    for room_id, idx in index["y"].items():
        room = rooms[str(room_id)]
        lower[idx] = (
            1.0 if (not case.allow_room_deactivation or room.protected_capacity_flag) else 0.0
        )
        upper[idx] = 1.0
        integrality[idx] = 1
    for building_id, idx in index["z"].items():
        del building_id
        lower[idx] = 1.0 if not case.allow_room_deactivation else 0.0
        upper[idx] = 1.0
        integrality[idx] = 1
    for key, idx in index["r"].items():
        service_id, period = key
        demand = _demand_lookup(demand_rows)[(service_id, period)]
        remote_share = 0.0
        if case.allow_remote_delivery and _bool_config(config.remote_delivery_limits["enabled"]):
            remote_share = min(
                demand.remote_eligible_rate,
                _float_config(config.remote_delivery_limits["maximum_remote_share"]),
            )
        upper[idx] = demand.planning_demand_hours * remote_share
    if _bool_config(config.service_continuity_rules["prohibit_unmet_mandatory_demand"]):
        for idx in index["u"].values():
            upper[idx] = 0.0
    for idx in index["m"].values():
        upper[idx] = 1.0
        integrality[idx] = 1
    del building_sites
    return lower, upper, integrality


def _constraints(
    config: OptimisationConfig,
    case: OptimisationCase,
    eligible: list[Candidate],
    demand_rows: list[DemandRow],
    rooms: dict[str, RoomCapacity],
    index: dict[str, dict[Any, int]],
) -> tuple[list[tuple[list[float], float, float]], list[dict[str, object]]]:
    rows: list[tuple[list[float], float, float]] = []
    specs: list[dict[str, object]] = []
    size = _variable_count(index)
    by_demand = _group_candidates(eligible, lambda item: (item.service_id, item.period))
    by_room_period = _group_candidates(eligible, lambda item: (item.target_room_id, item.period))
    for demand in demand_rows:
        key = (demand.service_id, demand.period)
        vector = [0.0] * size
        for candidate in by_demand.get(key, []):
            vector[index["x"][candidate.candidate_id]] = 1.0
        vector[index["r"][key]] = 1.0
        vector[index["u"][key]] = 1.0
        rows.append((vector, demand.planning_demand_hours, demand.planning_demand_hours))
        specs.append(
            _spec(
                demand_constraint(*key),
                "demand_satisfaction",
                "__".join(key),
                "=",
                demand.planning_demand_hours,
            )
        )
        minimum_face_to_face_share = _float_config(
            config.service_continuity_rules["minimum_face_to_face_share"]
        )
        floor = demand.planning_demand_hours * minimum_face_to_face_share
        vector = [0.0] * size
        for candidate in by_demand.get(key, []):
            vector[index["x"][candidate.candidate_id]] = 1.0
        vector[index["r"][key]] = minimum_face_to_face_share
        vector[index["u"][key]] = minimum_face_to_face_share
        rows.append((vector, floor, np.inf))
        specs.append(
            _spec(
                face_to_face_floor_constraint(*key),
                "face_to_face_floor",
                "__".join(key),
                ">=",
                floor,
            )
        )
        vector = [0.0] * size
        vector[index["r"][key]] = 1.0
        remote_limit = _remote_limit(config, case, demand)
        rows.append((vector, -np.inf, remote_limit))
        specs.append(
            _spec(remote_limit_constraint(*key), "remote_limit", "__".join(key), "<=", remote_limit)
        )
    periods = sorted({row.period for row in demand_rows})
    for room_id, room in sorted(rooms.items()):
        for period in periods:
            vector = [0.0] * size
            for candidate in by_room_period.get((room_id, period), []):
                vector[index["x"][candidate.candidate_id]] = 1.0
            vector[index["y"][room_id]] = -room.allocatable_capacity_hours
            rows.append((vector, -np.inf, 0.0))
            specs.append(
                _spec(
                    room_capacity_constraint(room_id, period),
                    "room_capacity",
                    f"{room_id}__{period}",
                    "<=",
                    0.0,
                )
            )
        vector = [0.0] * size
        vector[index["y"][room_id]] = 1.0
        vector[index["z"][room.building_id]] = -1.0
        rows.append((vector, -np.inf, 0.0))
        specs.append(
            _spec(
                building_activation_constraint(room_id), "building_activation", room_id, "<=", 0.0
            )
        )
        if room.protected_capacity_flag:
            vector = [0.0] * size
            vector[index["y"][room_id]] = 1.0
            rows.append((vector, 1.0, 1.0))
            specs.append(
                _spec(protected_room_constraint(room_id), "protected_capacity", room_id, "=", 1.0)
            )
    for candidate in eligible:
        vector = [0.0] * size
        vector[index["x"][candidate.candidate_id]] = 1.0
        vector[index["y"][candidate.target_room_id]] = -candidate.planning_demand_hours
        rows.append((vector, -np.inf, 0.0))
        specs.append(
            _spec(
                room_activation_constraint(candidate.candidate_id),
                "room_activation",
                candidate.candidate_id,
                "<=",
                0.0,
            )
        )
        move_key = (candidate.service_id, candidate.source_site_id, candidate.target_site_id)
        if move_key in index["m"]:
            vector = [0.0] * size
            vector[index["x"][candidate.candidate_id]] = 1.0
            vector[index["m"][move_key]] = -candidate.planning_demand_hours
            rows.append((vector, -np.inf, 0.0))
            specs.append(
                _spec(
                    move_activation_constraint(candidate.candidate_id),
                    "move_activation",
                    candidate.candidate_id,
                    "<=",
                    0.0,
                )
            )
    return rows, specs


def _allocation_rows(
    optimisation_run_id: str,
    case_id: str,
    eligible: list[Candidate],
    demand_rows: list[DemandRow],
    index: dict[str, dict[Any, int]],
    solution: np.ndarray,
) -> list[dict[str, object]]:
    rows = []
    remote = {key: solution[idx] for key, idx in index["r"].items()}
    unmet = {key: solution[idx] for key, idx in index["u"].items()}
    demand_seen: set[tuple[str, str]] = set()
    for candidate in eligible:
        value = solution[index["x"][candidate.candidate_id]]
        if value <= 1e-6:
            continue
        key = (candidate.service_id, candidate.period)
        include_remote = key not in demand_seen
        demand_seen.add(key)
        rows.append(
            {
                "optimisation_run_id": optimisation_run_id,
                "case_id": case_id,
                "candidate_id": candidate.candidate_id,
                "service_id": candidate.service_id,
                "period": candidate.period,
                "room_id": candidate.target_room_id,
                "building_id": candidate.target_building_id,
                "site_id": candidate.target_site_id,
                "allocated_hours": round(float(value), 4),
                "remote_hours": round(float(remote[key]), 4) if include_remote else 0.0,
                "unmet_demand_hours": round(float(unmet[key]), 4) if include_remote else 0.0,
            }
        )
    if not rows:
        for demand in demand_rows:
            key = (demand.service_id, demand.period)
            rows.append(
                {
                    "optimisation_run_id": optimisation_run_id,
                    "case_id": case_id,
                    "candidate_id": f"NO_ALLOCATION__{demand.service_id}__{demand.period}",
                    "service_id": demand.service_id,
                    "period": demand.period,
                    "room_id": "none",
                    "building_id": "none",
                    "site_id": demand.source_site_id,
                    "allocated_hours": 0.0,
                    "remote_hours": round(float(remote[key]), 4),
                    "unmet_demand_hours": round(float(unmet[key]), 4),
                }
            )
    return sorted(rows, key=lambda row: str(row["candidate_id"]))


def _variable_rows(
    optimisation_run_id: str,
    case_id: str,
    index: dict[str, dict[Any, int]],
    lower: list[float],
    upper: list[float],
    solution: np.ndarray,
) -> list[dict[str, object]]:
    rows = []
    for variable_type, mapping in index.items():
        for variable_id, idx in sorted(mapping.items(), key=lambda item: str(item[0])):
            rows.append(
                {
                    "optimisation_run_id": optimisation_run_id,
                    "case_id": case_id,
                    "variable_id": f"{variable_type}__{variable_id}",
                    "variable_type": variable_type,
                    "lower_bound": round(float(lower[idx]), 4),
                    "upper_bound": None if np.isinf(upper[idx]) else round(float(upper[idx]), 4),
                    "value": round(float(solution[idx]), 4),
                }
            )
    return rows


def _room_status_rows(
    optimisation_run_id: str,
    case_id: str,
    rooms: dict[str, RoomCapacity],
    index: dict[str, dict[Any, int]],
    solution: np.ndarray,
) -> list[dict[str, object]]:
    return [
        {
            "optimisation_run_id": optimisation_run_id,
            "case_id": case_id,
            "room_id": room_id,
            "building_id": room.building_id,
            "active_value": round(float(solution[index["y"][room_id]]), 4),
            "protected_capacity_flag": 1 if room.protected_capacity_flag else 0,
            "status": "active" if solution[index["y"][room_id]] >= 0.5 else "inactive_candidate",
        }
        for room_id, room in sorted(rooms.items())
    ]


def _building_status_rows(
    optimisation_run_id: str,
    case_id: str,
    building_sites: dict[str, str],
    rooms: dict[str, RoomCapacity],
    index: dict[str, dict[Any, int]],
    solution: np.ndarray,
) -> list[dict[str, object]]:
    grouped = _group_room_ids_by_building(rooms)
    rows = []
    for building_id, site_id in sorted(building_sites.items()):
        releasable = all(solution[index["y"][room_id]] < 0.5 for room_id in grouped[building_id])
        rows.append(
            {
                "optimisation_run_id": optimisation_run_id,
                "case_id": case_id,
                "building_id": building_id,
                "site_id": site_id,
                "active_value": round(float(solution[index["z"][building_id]]), 4),
                "potentially_releasable_flag": 1 if releasable else 0,
                "status": "potentially releasable in the mathematical candidate"
                if releasable
                else "active",
            }
        )
    return rows


def _service_move_rows(
    optimisation_run_id: str,
    case_id: str,
    eligible: list[Candidate],
    index: dict[str, dict[Any, int]],
    solution: np.ndarray,
) -> list[dict[str, object]]:
    moved_hours: dict[tuple[str, str, str], float] = defaultdict(float)
    for candidate in eligible:
        if candidate.source_site_id == candidate.target_site_id:
            continue
        key = (candidate.service_id, candidate.source_site_id, candidate.target_site_id)
        moved_hours[key] += float(solution[index["x"][candidate.candidate_id]])
    rows = []
    for key, idx in sorted(index["m"].items()):
        rows.append(
            {
                "optimisation_run_id": optimisation_run_id,
                "case_id": case_id,
                "service_id": key[0],
                "source_site_id": key[1],
                "target_site_id": key[2],
                "move_value": round(float(solution[idx]), 4),
                "moved_hours": round(moved_hours[key], 4),
                "status": "candidate_move" if solution[idx] >= 0.5 else "not_moved",
            }
        )
    return rows


def _constraint_rows(
    optimisation_run_id: str,
    case_id: str,
    specs: list[dict[str, object]],
    constraints: list[tuple[list[float], float, float]],
    solution: np.ndarray,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    rows = []
    for spec, (vector, lower, upper) in zip(specs, constraints, strict=True):
        activity = float(np.dot(np.array(vector), solution))
        if np.isneginf(lower):
            slack = upper - activity
            rhs = upper
        elif np.isposinf(upper):
            slack = activity - lower
            rhs = lower
        else:
            slack = abs(activity - lower)
            rhs = lower
        row = {
            "optimisation_run_id": optimisation_run_id,
            "case_id": case_id,
            "constraint_id": spec["constraint_id"],
            "constraint_family": spec["constraint_family"],
            "entity_id": spec["entity_id"],
            "sense": spec["sense"],
            "rhs": round(float(rhs), 4),
            "activity_value": round(activity, 4),
            "slack_value": round(float(slack), 4),
            "binding_flag": 1 if abs(slack) <= 1e-5 else 0,
            "result_status": "pass" if slack >= -1e-5 else "fail",
        }
        rows.append(row)
    binding = [
        {
            "optimisation_run_id": row["optimisation_run_id"],
            "case_id": row["case_id"],
            "constraint_id": row["constraint_id"],
            "constraint_family": row["constraint_family"],
            "entity_id": row["entity_id"],
            "slack_value": row["slack_value"],
        }
        for row in rows
        if row["binding_flag"] == 1
    ]
    return rows, binding


def _objective_component_rows(
    optimisation_run_id: str,
    case_id: str,
    config: OptimisationConfig,
    eligible: list[Candidate],
    demand_rows: list[DemandRow],
    rooms: dict[str, RoomCapacity],
    room_recurring_costs: dict[str, float],
    index: dict[str, dict[Any, int]],
    solution: np.ndarray,
) -> list[dict[str, object]]:
    del demand_rows
    cost = config.cost_coefficients
    weights = config.objective_weights
    room_allocation = {
        room_id: sum(
            solution[index["x"][candidate.candidate_id]]
            for candidate in eligible
            if candidate.target_room_id == room_id
        )
        for room_id in rooms
    }
    components = {
        "retained_recurring_estate_cost": weights["retained_recurring_estate_cost"]
        * sum(room_recurring_costs[room_id] * solution[index["y"][room_id]] for room_id in rooms),
        "room_activation_cost": weights["room_activation_cost"]
        * cost["room_activation_cost_per_room"]
        * sum(solution[idx] for idx in index["y"].values()),
        "service_relocation_cost": weights["service_relocation_cost"]
        * cost["service_relocation_cost_per_move"]
        * sum(solution[idx] for idx in index["m"].values()),
        "travel_penalty": weights["travel_penalty"]
        * cost["travel_penalty_per_km_hour"]
        * sum(
            candidate.travel_penalty * solution[index["x"][candidate.candidate_id]]
            for candidate in eligible
        ),
        "disruption_penalty": weights["disruption_penalty"]
        * cost["disruption_penalty_per_moved_hour"]
        * sum(
            candidate.disruption_penalty * solution[index["x"][candidate.candidate_id]]
            for candidate in eligible
        ),
        "underutilisation_penalty": weights["underutilisation_penalty"]
        * cost["underutilisation_penalty_per_unused_hour"]
        * sum(
            rooms[room_id].allocatable_capacity_hours * solution[index["y"][room_id]]
            - room_allocation[room_id]
            for room_id in rooms
        ),
        "unmet_demand_penalty": weights["unmet_demand_penalty"]
        * cost["unmet_demand_penalty_per_hour"]
        * sum(solution[idx] for idx in index["u"].values()),
        "workforce_warning_penalty": 0.0,
        "accessibility_warning_penalty": 0.0,
        "deterministic_tie_breaker": cost["deterministic_tie_breaker"]
        * sum(
            (index["x"][candidate.candidate_id] + 1) * solution[index["x"][candidate.candidate_id]]
            for candidate in eligible
        ),
    }
    return [
        {
            "optimisation_run_id": optimisation_run_id,
            "case_id": case_id,
            "component": component,
            "component_value": round(float(value), 4),
            "coefficient": _component_coefficient(config, component),
            "unit": OBJECTIVE_UNITS[component],
        }
        for component, value in sorted(components.items())
    ]


def _case_result(
    *,
    case_id: str,
    native_status: str,
    objective_value: float,
    demand_rows: list[DemandRow],
    allocations: list[dict[str, object]],
    room_status: list[dict[str, object]],
    building_status: list[dict[str, object]],
    service_moves: list[dict[str, object]],
) -> SolverCaseResult:
    allocated = sum(_row_float(row, "allocated_hours") for row in allocations)
    remote = sum(_row_float(row, "remote_hours") for row in allocations)
    unmet = sum(_row_float(row, "unmet_demand_hours") for row in allocations)
    if not allocations:
        unmet = sum(row.planning_demand_hours for row in demand_rows)
    return SolverCaseResult(
        case_id=case_id,
        solver_status=map_solver_status(native_status, unmet),
        native_status=native_status,
        objective_value=objective_value,
        objective_gap=0.0,
        allocated_demand_hours=allocated,
        unmet_demand_hours=unmet,
        remote_demand_hours=remote,
        active_rooms=sum(1 for row in room_status if _row_float(row, "active_value") >= 0.5),
        inactive_rooms=sum(1 for row in room_status if _row_float(row, "active_value") < 0.5),
        active_buildings=sum(
            1 for row in building_status if _row_float(row, "active_value") >= 0.5
        ),
        potentially_releasable_buildings=sum(
            1 for row in building_status if _row_int(row, "potentially_releasable_flag") == 1
        ),
        services_moved=sum(1 for row in service_moves if _row_float(row, "move_value") >= 0.5),
        solve_diagnostics="solver completed and evidence extracted",
    )


def _infeasibility_rows(
    optimisation_run_id: str,
    case_id: str,
    result: SolverCaseResult,
    demand_rows: list[DemandRow],
    eligible: list[Candidate],
    rooms: dict[str, RoomCapacity],
    candidates: list[Candidate],
) -> list[dict[str, object]]:
    rows = []
    index = 1
    by_demand = _group_candidates(eligible, lambda item: (item.service_id, item.period))
    for demand in demand_rows:
        eligible_capacity = sum(
            rooms[item.target_room_id].allocatable_capacity_hours
            for item in by_demand.get((demand.service_id, demand.period), [])
        )
        if eligible_capacity + 1e-5 < demand.planning_demand_hours:
            rows.append(
                {
                    "optimisation_run_id": optimisation_run_id,
                    "case_id": case_id,
                    "diagnostic_id": f"DIAG-{index:04d}",
                    "diagnostic_type": "service_period_capacity_shortfall",
                    "entity_id": f"{demand.service_id}__{demand.period}",
                    "shortfall_value": round(demand.planning_demand_hours - eligible_capacity, 4),
                    "detail": "service-period demand exceeds eligible candidate capacity",
                }
            )
            index += 1
    blocked: dict[str, int] = defaultdict(int)
    for candidate in candidates:
        if candidate.exclusion_reason:
            for reason in candidate.exclusion_reason.split(";"):
                blocked[reason] += 1
    for reason, count in sorted(blocked.items()):
        rows.append(
            {
                "optimisation_run_id": optimisation_run_id,
                "case_id": case_id,
                "diagnostic_id": f"DIAG-{index:04d}",
                "diagnostic_type": reason,
                "entity_id": "candidate_catalogue",
                "shortfall_value": float(count),
                "detail": f"{count} candidates blocked by {reason}",
            }
        )
        index += 1
    if result.solver_status in {"optimal", "feasible"}:
        return [row for row in rows if str(row["diagnostic_type"]).endswith("blocked")]
    return rows


def _remote_limit(config: OptimisationConfig, case: OptimisationCase, demand: DemandRow) -> float:
    if not case.allow_remote_delivery or not _bool_config(config.remote_delivery_limits["enabled"]):
        return 0.0
    return demand.planning_demand_hours * min(
        demand.remote_eligible_rate,
        _float_config(config.remote_delivery_limits["maximum_remote_share"]),
    )


def _spec(
    constraint_id: str, family: str, entity_id: str, sense: str, rhs: float
) -> dict[str, object]:
    return {
        "constraint_id": constraint_id,
        "constraint_family": family,
        "entity_id": entity_id,
        "sense": sense,
        "rhs": rhs,
    }


def _variable_count(index: dict[str, dict[Any, int]]) -> int:
    return sum(len(values) for values in index.values())


def _demand_lookup(demand_rows: list[DemandRow]) -> dict[tuple[str, str], DemandRow]:
    return {(row.service_id, row.period): row for row in demand_rows}


def _group_candidates(candidates: list[Candidate], key_fn: Any) -> dict[Any, list[Candidate]]:
    grouped: dict[Any, list[Candidate]] = defaultdict(list)
    for candidate in candidates:
        grouped[key_fn(candidate)].append(candidate)
    return dict(grouped)


def _group_room_ids_by_building(rooms: dict[str, RoomCapacity]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for room_id, room in rooms.items():
        grouped[room.building_id].append(room_id)
    return dict(grouped)


def _component_coefficient(config: OptimisationConfig, component: str) -> float:
    mapping = {
        "retained_recurring_estate_cost": 1.0,
        "room_activation_cost": config.cost_coefficients["room_activation_cost_per_room"],
        "service_relocation_cost": config.cost_coefficients["service_relocation_cost_per_move"],
        "travel_penalty": config.cost_coefficients["travel_penalty_per_km_hour"],
        "disruption_penalty": config.cost_coefficients["disruption_penalty_per_moved_hour"],
        "underutilisation_penalty": config.cost_coefficients[
            "underutilisation_penalty_per_unused_hour"
        ],
        "unmet_demand_penalty": config.cost_coefficients["unmet_demand_penalty_per_hour"],
        "workforce_warning_penalty": config.cost_coefficients["workforce_warning_penalty"],
        "accessibility_warning_penalty": config.cost_coefficients["accessibility_warning_penalty"],
        "deterministic_tie_breaker": config.cost_coefficients["deterministic_tie_breaker"],
    }
    return float(mapping[component])


def _row_float(row: dict[str, object], column: str) -> float:
    value = row[column]
    if isinstance(value, int | float | str):
        return float(value)
    raise TypeError(f"Expected numeric row value for {column}, got {type(value)}")


def _row_int(row: dict[str, object], column: str) -> int:
    value = row[column]
    if isinstance(value, int | str):
        return int(value)
    raise TypeError(f"Expected integer row value for {column}, got {type(value)}")


def _float_config(value: object) -> float:
    if isinstance(value, int | float | str):
        return float(value)
    raise TypeError(f"Expected numeric optimisation configuration value, got {type(value)}")


def _bool_config(value: object) -> bool:
    return str(value).lower() == "true"
