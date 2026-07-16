"""Milestone 7 deterministic scenario engine."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

from estate_intelligence.forecasting.engine import verify_forecasting
from estate_intelligence.ingestion.database import connect
from estate_intelligence.scenarios.evaluator import evaluate_scenario
from estate_intelligence.scenarios.models import ScenarioConfig
from estate_intelligence.scenarios.reporting import export_scenario_evidence

SCENARIO_TABLES = (
    "evidence_scenario_runs",
    "evidence_scenario_catalogue",
    "evidence_scenario_candidates",
    "evidence_scenario_room_actions",
    "evidence_scenario_service_moves",
    "evidence_scenario_capacity",
    "evidence_scenario_compatibility",
    "evidence_scenario_workforce",
    "evidence_scenario_accessibility",
    "evidence_scenario_costs",
    "evidence_scenario_constraints",
    "evidence_scenario_risks",
    "evidence_scenario_scores",
    "evidence_scenario_comparison",
)


def run_scenarios(
    *,
    database_path: Path,
    config_path: Path = Path("config/scenarios.yaml"),
    output_dir: Path | None = None,
    rebuild: bool = False,
) -> dict[str, Any]:
    """Run deterministic scenario analysis."""

    verify_forecasting(database_path)
    config = ScenarioConfig.from_yaml(config_path)
    connection = connect(database_path)
    try:
        run_ids = _source_run_ids(connection)
        config_checksum = _file_checksum(config_path)
        catalogue_checksum = _stable_checksum(
            [item.model_dump() for item in config.scenario_catalogue]
        )
        constraint_checksum = _stable_checksum(
            {
                "room": config.room_compatibility_rules,
                "workforce": config.workforce_constraints,
                "accessibility": config.accessibility_constraints,
                "continuity": config.service_continuity_rules,
                "protected": config.protected_capacity_policy,
            }
        )
        scenario_run_id = _scenario_run_id(
            config.framework_version,
            run_ids["ingestion_run_id"],
            run_ids["quality_run_id"],
            run_ids["utilisation_run_id"],
            run_ids["forecast_run_id"],
            config_checksum,
            catalogue_checksum,
            constraint_checksum,
        )
        with connection:
            _create_scenario_tables(connection)
            if rebuild:
                _clear_scenario_tables(connection)
            elif _scenario_run_exists(connection, scenario_run_id):
                raise FileExistsError(
                    "Refusing to overwrite existing scenario evidence without --rebuild"
                )
            catalogue_rows = [
                {
                    "scenario_run_id": scenario_run_id,
                    "scenario_id": item.scenario_id,
                    "scenario_type": item.scenario_type,
                    "label": item.label,
                }
                for item in config.scenario_catalogue
            ]
            _insert_rows(connection, "evidence_scenario_catalogue", catalogue_rows)
            for scenario in config.scenario_catalogue:
                evidence = evaluate_scenario(connection, scenario, scenario_run_id, config)
                _insert_evidence(connection, evidence)
            readiness = _readiness(connection)
            connection.execute(
                """
                INSERT INTO evidence_scenario_runs
                (scenario_run_id, ingestion_run_id, quality_run_id, utilisation_run_id,
                 forecast_run_id, framework_version, config_checksum,
                 scenario_catalogue_checksum, constraint_catalogue_checksum,
                 demand_basis, interval_basis, readiness_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    scenario_run_id,
                    run_ids["ingestion_run_id"],
                    run_ids["quality_run_id"],
                    run_ids["utilisation_run_id"],
                    run_ids["forecast_run_id"],
                    config.framework_version,
                    config_checksum,
                    catalogue_checksum,
                    constraint_checksum,
                    config.forecast_demand_basis,
                    config.forecast_interval_basis,
                    readiness,
                ),
            )
        exports: dict[str, str] = {}
        if output_dir is not None:
            exports = {
                name: str(path)
                for name, path in export_scenario_evidence(
                    connection, output_dir, scenario_run_id
                ).items()
            }
        return {
            "scenario_run_id": scenario_run_id,
            **run_ids,
            "config_checksum": config_checksum,
            "scenario_catalogue_checksum": catalogue_checksum,
            "constraint_catalogue_checksum": constraint_checksum,
            "scenario_count": len(config.scenario_catalogue),
            "readiness_status": readiness,
            "exports": exports,
        }
    finally:
        connection.close()


def verify_scenarios(database_path: Path) -> dict[str, Any]:
    """Verify persisted scenario evidence."""

    connection = connect(database_path)
    try:
        run = connection.execute(
            "SELECT * FROM evidence_scenario_runs ORDER BY scenario_run_id LIMIT 1"
        ).fetchone()
        if run is None:
            raise ValueError("No scenario run evidence found")
        count = connection.execute(
            "SELECT COUNT(*) AS count FROM evidence_scenario_comparison"
        ).fetchone()["count"]
        constraints = connection.execute(
            "SELECT COUNT(*) AS count FROM evidence_scenario_constraints"
        ).fetchone()["count"]
        if count != 4 or constraints == 0:
            raise ValueError("Scenario evidence is incomplete")
        return {
            "scenario_run_id": run["scenario_run_id"],
            "readiness_status": run["readiness_status"],
            "scenario_count": count,
            "constraint_count": constraints,
        }
    finally:
        connection.close()


def export_existing_scenario_evidence(database_path: Path, output_dir: Path) -> dict[str, Path]:
    """Export persisted scenario evidence."""

    connection = connect(database_path)
    try:
        row = connection.execute(
            "SELECT scenario_run_id FROM evidence_scenario_runs ORDER BY scenario_run_id LIMIT 1"
        ).fetchone()
        if row is None:
            raise ValueError("No scenario run evidence found")
        return export_scenario_evidence(connection, output_dir, row["scenario_run_id"])
    finally:
        connection.close()


def _insert_evidence(
    connection: sqlite3.Connection, evidence: dict[str, list[dict[str, Any]]]
) -> None:
    mapping = {
        "candidates": "evidence_scenario_candidates",
        "room_actions": "evidence_scenario_room_actions",
        "service_moves": "evidence_scenario_service_moves",
        "capacity": "evidence_scenario_capacity",
        "compatibility": "evidence_scenario_compatibility",
        "workforce": "evidence_scenario_workforce",
        "accessibility": "evidence_scenario_accessibility",
        "costs": "evidence_scenario_costs",
        "constraints": "evidence_scenario_constraints",
        "risks": "evidence_scenario_risks",
        "scores": "evidence_scenario_scores",
        "comparison": "evidence_scenario_comparison",
    }
    for key, table in mapping.items():
        _insert_rows(connection, table, evidence[key])


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


def _create_scenario_tables(connection: sqlite3.Connection) -> None:
    connection.executescript(
        Path("database/schema/009_scenario_tables.sql").read_text(encoding="utf-8")
    )


def _clear_scenario_tables(connection: sqlite3.Connection) -> None:
    for table in SCENARIO_TABLES:
        connection.execute(f"DELETE FROM {table}")


def _scenario_run_exists(connection: sqlite3.Connection, scenario_run_id: str) -> bool:
    return (
        connection.execute(
            "SELECT scenario_run_id FROM evidence_scenario_runs WHERE scenario_run_id = ?",
            (scenario_run_id,),
        ).fetchone()
        is not None
    )


def _readiness(connection: sqlite3.Connection) -> str:
    rows = connection.execute(
        "SELECT feasibility_status FROM evidence_scenario_comparison"
    ).fetchall()
    if any(row["feasibility_status"] == "infeasible" for row in rows):
        return "review_required"
    return "scenario_evidence_ready"


def _source_run_ids(connection: sqlite3.Connection) -> dict[str, str]:
    queries = {
        "ingestion_run_id": (
            "SELECT ingestion_run_id AS id "
            "FROM evidence_ingestion_runs "
            "ORDER BY ingestion_run_id LIMIT 1"
        ),
        "quality_run_id": (
            "SELECT quality_run_id AS id FROM evidence_quality_runs ORDER BY quality_run_id LIMIT 1"
        ),
        "utilisation_run_id": (
            "SELECT utilisation_run_id AS id "
            "FROM evidence_utilisation_runs "
            "ORDER BY utilisation_run_id LIMIT 1"
        ),
        "forecast_run_id": (
            "SELECT forecast_run_id AS id "
            "FROM evidence_forecast_runs "
            "ORDER BY forecast_run_id LIMIT 1"
        ),
    }
    result = {}
    for key, query in queries.items():
        row = connection.execute(query).fetchone()
        if row is None:
            raise ValueError("Ingestion, quality, utilisation and forecast evidence are required")
        result[key] = str(row["id"])
    return result


def _scenario_run_id(*parts: str) -> str:
    digest = hashlib.sha256(json.dumps(parts, sort_keys=True).encode()).hexdigest()
    return f"SCN-{digest[:16]}"


def _file_checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _stable_checksum(payload: object) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
