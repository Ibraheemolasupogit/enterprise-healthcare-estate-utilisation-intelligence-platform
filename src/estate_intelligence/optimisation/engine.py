"""Milestone 8 deterministic optimisation engine."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

from estate_intelligence.ingestion.database import connect
from estate_intelligence.optimisation.candidates import build_candidates
from estate_intelligence.optimisation.model import solve_case
from estate_intelligence.optimisation.models import Candidate, OptimisationConfig
from estate_intelligence.optimisation.reporting import export_optimisation_evidence
from estate_intelligence.optimisation.solver import solver_identity
from estate_intelligence.scenarios.engine import verify_scenarios

OPTIMISATION_TABLES = (
    "evidence_optimisation_runs",
    "evidence_optimisation_cases",
    "evidence_optimisation_candidates",
    "evidence_optimisation_variables",
    "evidence_optimisation_allocations",
    "evidence_optimisation_room_status",
    "evidence_optimisation_building_status",
    "evidence_optimisation_service_moves",
    "evidence_optimisation_constraints",
    "evidence_optimisation_binding_constraints",
    "evidence_optimisation_objective_components",
    "evidence_optimisation_solver_results",
    "evidence_optimisation_infeasibility",
    "evidence_optimisation_comparison",
)


def run_optimisation(
    *,
    database_path: Path,
    config_path: Path = Path("config/optimisation.yaml"),
    output_dir: Path | None = None,
    rebuild: bool = False,
) -> dict[str, Any]:
    """Run deterministic constrained estate allocation optimisation."""

    verify_scenarios(database_path)
    config = OptimisationConfig.from_yaml(config_path)
    connection = connect(database_path)
    try:
        run_ids = _source_run_ids(connection)
        config_checksum = _file_checksum(config_path)
        candidates, demand_rows, rooms = build_candidates(
            connection,
            config,
            forecast_run_id=run_ids["forecast_run_id"],
            scenario_run_id=run_ids["scenario_run_id"],
        )
        candidate_checksum = _stable_checksum([item.model_dump() for item in candidates])
        constraint_checksum = _stable_checksum(
            {
                "capacity_buffer": config.capacity_buffer,
                "contingency_capacity": config.contingency_capacity,
                "service_continuity": config.service_continuity_rules,
                "workforce": config.workforce_constraints,
                "accessibility": config.accessibility_constraints,
                "protected": config.protected_capacity_policy,
            }
        )
        objective_checksum = _stable_checksum(
            {
                "weights": config.objective_weights,
                "coefficients": config.cost_coefficients,
            }
        )
        solver_id = solver_identity(
            config.solver,
            config.solver_threads,
            config.solver_time_limit_seconds,
            config.solver_mip_gap,
        )
        optimisation_run_id = _optimisation_run_id(
            config.framework_version,
            run_ids["ingestion_run_id"],
            run_ids["quality_run_id"],
            run_ids["utilisation_run_id"],
            run_ids["forecast_run_id"],
            run_ids["scenario_run_id"],
            config_checksum,
            candidate_checksum,
            constraint_checksum,
            objective_checksum,
            solver_id,
        )
        building_sites = {room.building_id: room.site_id for room in rooms.values()}
        room_costs = _room_recurring_costs(connection, rooms)
        with connection:
            _create_tables(connection)
            if rebuild:
                _clear_tables(connection)
            elif _run_exists(connection, optimisation_run_id):
                raise FileExistsError(
                    "Refusing to overwrite existing optimisation evidence without --rebuild"
                )
            _insert_cases(connection, optimisation_run_id, config)
            _insert_rows(
                connection,
                "evidence_optimisation_candidates",
                [_candidate_row(optimisation_run_id, item) for item in candidates],
            )
            case_statuses: list[str] = []
            for case in config.optimisation_cases:
                evidence = solve_case(
                    optimisation_run_id=optimisation_run_id,
                    case=case,
                    config=config,
                    candidates=candidates,
                    demand_rows=demand_rows,
                    rooms=rooms,
                    building_sites=building_sites,
                    room_recurring_costs=room_costs,
                )
                _insert_evidence(connection, evidence.model_dump())
                case_statuses.extend(str(row["mapped_status"]) for row in evidence.solver_results)
            readiness = (
                "optimisation_evidence_ready"
                if all(status in {"optimal", "feasible"} for status in case_statuses)
                else "review_required"
            )
            connection.execute(
                """
                INSERT INTO evidence_optimisation_runs
                (optimisation_run_id, ingestion_run_id, quality_run_id, utilisation_run_id,
                 forecast_run_id, scenario_run_id, framework_version, config_checksum,
                 candidate_catalogue_checksum, constraint_catalogue_checksum,
                 objective_catalogue_checksum, solver_identity, planning_demand_basis,
                 readiness_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    optimisation_run_id,
                    run_ids["ingestion_run_id"],
                    run_ids["quality_run_id"],
                    run_ids["utilisation_run_id"],
                    run_ids["forecast_run_id"],
                    run_ids["scenario_run_id"],
                    config.framework_version,
                    config_checksum,
                    candidate_checksum,
                    constraint_checksum,
                    objective_checksum,
                    solver_id,
                    config.planning_demand_basis.target,
                    readiness,
                ),
            )
        exports: dict[str, str] = {}
        if output_dir is not None:
            exports = {
                name: str(path)
                for name, path in export_optimisation_evidence(
                    connection, output_dir, optimisation_run_id
                ).items()
            }
        return {
            "optimisation_run_id": optimisation_run_id,
            **run_ids,
            "config_checksum": config_checksum,
            "candidate_catalogue_checksum": candidate_checksum,
            "constraint_catalogue_checksum": constraint_checksum,
            "objective_catalogue_checksum": objective_checksum,
            "solver_identity": solver_id,
            "case_count": len(config.optimisation_cases),
            "candidate_count": len(candidates),
            "readiness_status": readiness,
            "exports": exports,
        }
    finally:
        connection.close()


def verify_optimisation(database_path: Path) -> dict[str, Any]:
    """Verify persisted optimisation evidence."""

    connection = connect(database_path)
    try:
        run = connection.execute(
            "SELECT * FROM evidence_optimisation_runs ORDER BY optimisation_run_id LIMIT 1"
        ).fetchone()
        if run is None:
            raise ValueError("No optimisation run evidence found")
        cases = connection.execute(
            "SELECT COUNT(*) AS count FROM evidence_optimisation_comparison"
        ).fetchone()["count"]
        candidates = connection.execute(
            "SELECT COUNT(*) AS count FROM evidence_optimisation_candidates"
        ).fetchone()["count"]
        unmet = connection.execute(
            "SELECT COALESCE(SUM(unmet_demand_hours), 0) AS unmet "
            "FROM evidence_optimisation_comparison"
        ).fetchone()["unmet"]
        if cases != 4 or candidates == 0:
            raise ValueError("Optimisation evidence is incomplete")
        return {
            "optimisation_run_id": run["optimisation_run_id"],
            "readiness_status": run["readiness_status"],
            "case_count": cases,
            "candidate_count": candidates,
            "unmet_demand_hours": round(float(unmet), 4),
        }
    finally:
        connection.close()


def export_existing_optimisation_evidence(database_path: Path, output_dir: Path) -> dict[str, Path]:
    """Export persisted optimisation evidence."""

    connection = connect(database_path)
    try:
        row = connection.execute(
            "SELECT optimisation_run_id FROM evidence_optimisation_runs "
            "ORDER BY optimisation_run_id LIMIT 1"
        ).fetchone()
        if row is None:
            raise ValueError("No optimisation run evidence found")
        return export_optimisation_evidence(connection, output_dir, row["optimisation_run_id"])
    finally:
        connection.close()


def _insert_evidence(connection: sqlite3.Connection, evidence: dict[str, Any]) -> None:
    mapping = {
        "variables": "evidence_optimisation_variables",
        "allocations": "evidence_optimisation_allocations",
        "room_status": "evidence_optimisation_room_status",
        "building_status": "evidence_optimisation_building_status",
        "service_moves": "evidence_optimisation_service_moves",
        "constraints": "evidence_optimisation_constraints",
        "binding_constraints": "evidence_optimisation_binding_constraints",
        "objective_components": "evidence_optimisation_objective_components",
        "solver_results": "evidence_optimisation_solver_results",
        "infeasibility": "evidence_optimisation_infeasibility",
        "comparison": "evidence_optimisation_comparison",
    }
    for key, table in mapping.items():
        _insert_rows(connection, table, evidence[key])


def _insert_cases(
    connection: sqlite3.Connection, optimisation_run_id: str, config: OptimisationConfig
) -> None:
    _insert_rows(
        connection,
        "evidence_optimisation_cases",
        [
            {
                "optimisation_run_id": optimisation_run_id,
                "case_id": case.case_id,
                "label": case.label,
                "allow_room_deactivation": 1 if case.allow_room_deactivation else 0,
                "allow_site_movement": 1 if case.allow_site_movement else 0,
                "allow_remote_delivery": 1 if case.allow_remote_delivery else 0,
            }
            for case in config.optimisation_cases
        ],
    )


def _candidate_row(optimisation_run_id: str, candidate: Candidate) -> dict[str, object]:
    row = candidate.model_dump()
    row["optimisation_run_id"] = optimisation_run_id
    for key, value in list(row.items()):
        if isinstance(value, bool):
            row[key] = 1 if value else 0
    return row


def _insert_rows(connection: sqlite3.Connection, table: str, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    table_columns = {
        row["name"] for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
    }
    for row in rows:
        clean = {key: value for key, value in row.items() if key in table_columns}
        columns = list(clean)
        placeholders = ", ".join("?" for _ in columns)
        connection.execute(
            f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})",
            tuple(clean[column] for column in columns),
        )


def _create_tables(connection: sqlite3.Connection) -> None:
    connection.executescript(
        Path("database/schema/010_optimisation_tables.sql").read_text(encoding="utf-8")
    )


def _clear_tables(connection: sqlite3.Connection) -> None:
    for table in OPTIMISATION_TABLES:
        connection.execute(f"DELETE FROM {table}")


def _run_exists(connection: sqlite3.Connection, optimisation_run_id: str) -> bool:
    return (
        connection.execute(
            "SELECT optimisation_run_id FROM evidence_optimisation_runs "
            "WHERE optimisation_run_id = ?",
            (optimisation_run_id,),
        ).fetchone()
        is not None
    )


def _source_run_ids(connection: sqlite3.Connection) -> dict[str, str]:
    queries = {
        "ingestion_run_id": (
            "SELECT ingestion_run_id AS id "
            "FROM evidence_ingestion_runs ORDER BY ingestion_run_id LIMIT 1"
        ),
        "quality_run_id": (
            "SELECT quality_run_id AS id FROM evidence_quality_runs ORDER BY quality_run_id LIMIT 1"
        ),
        "utilisation_run_id": (
            "SELECT utilisation_run_id AS id "
            "FROM evidence_utilisation_runs ORDER BY utilisation_run_id LIMIT 1"
        ),
        "forecast_run_id": (
            "SELECT forecast_run_id AS id "
            "FROM evidence_forecast_runs ORDER BY forecast_run_id LIMIT 1"
        ),
        "scenario_run_id": (
            "SELECT scenario_run_id AS id "
            "FROM evidence_scenario_runs ORDER BY scenario_run_id LIMIT 1"
        ),
    }
    result = {}
    for key, query in queries.items():
        row = connection.execute(query).fetchone()
        if row is None:
            raise ValueError(
                "Ingestion, quality, utilisation, forecast and scenario evidence are required"
            )
        result[key] = str(row["id"])
    return result


def _room_recurring_costs(
    connection: sqlite3.Connection, rooms: dict[str, Any]
) -> dict[str, float]:
    cost_by_building = {
        row["building_id"]: float(row["annual_operating_cost"]) / 12
        for row in connection.execute(
            "SELECT building_id, annual_operating_cost FROM evidence_unit_cost_metrics"
        )
    }
    counts: dict[str, int] = {}
    for room in rooms.values():
        counts[room.building_id] = counts.get(room.building_id, 0) + 1
    return {
        room_id: round(cost_by_building.get(room.building_id, 0.0) / counts[room.building_id], 4)
        for room_id, room in rooms.items()
    }


def _optimisation_run_id(*parts: str) -> str:
    digest = hashlib.sha256(json.dumps(parts, sort_keys=True).encode()).hexdigest()
    return f"OPT-{digest[:16]}"


def _file_checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _stable_checksum(payload: object) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
