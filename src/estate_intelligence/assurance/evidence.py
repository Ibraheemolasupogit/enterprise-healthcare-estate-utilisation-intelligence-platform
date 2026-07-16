"""Assurance database helpers."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from estate_intelligence.ingestion.database import connect, execute_sql_file
from estate_intelligence.utils.paths import repository_root

RUN_TABLES: dict[str, tuple[str, str]] = {
    "ingestion": ("evidence_ingestion_runs", "ingestion_run_id"),
    "quality": ("evidence_quality_runs", "quality_run_id"),
    "utilisation": ("evidence_utilisation_runs", "utilisation_run_id"),
    "forecast": ("evidence_forecast_runs", "forecast_run_id"),
    "scenario": ("evidence_scenario_runs", "scenario_run_id"),
    "optimisation": ("evidence_optimisation_runs", "optimisation_run_id"),
    "simulation": ("evidence_simulation_runs", "simulation_run_id"),
    "financial": ("evidence_financial_runs", "financial_run_id"),
    "communication": ("evidence_communication_runs", "communication_run_id"),
}


def open_assurance_connection(database_path: Path) -> sqlite3.Connection:
    connection = connect(database_path)
    execute_sql_file(
        connection, repository_root() / "database" / "schema" / "014_assurance_tables.sql"
    )
    return connection


def fetch_all(
    connection: sqlite3.Connection,
    sql: str,
    parameters: tuple[Any, ...] = (),
) -> list[dict[str, Any]]:
    return [dict(row) for row in connection.execute(sql, parameters).fetchall()]


def latest_run_lineage(connection: sqlite3.Connection) -> dict[str, str]:
    lineage: dict[str, str] = {}
    for run_type, (table, column) in RUN_TABLES.items():
        row = connection.execute(
            f"SELECT {column} AS run_id FROM {table} ORDER BY {column} DESC LIMIT 1"
        ).fetchone()
        if row:
            lineage[run_type] = str(row["run_id"])
    missing = sorted(set(RUN_TABLES) - set(lineage))
    if missing:
        raise ValueError(f"Missing upstream run evidence: {missing}")
    return lineage
