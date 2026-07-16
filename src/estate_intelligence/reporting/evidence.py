"""Evidence loading helpers for the communication service."""

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
}


def ensure_communication_schema(connection: sqlite3.Connection) -> None:
    execute_sql_file(
        connection, repository_root() / "database" / "schema" / "013_communication_tables.sql"
    )


def open_connection(database_path: Path) -> sqlite3.Connection:
    connection = connect(database_path)
    ensure_communication_schema(connection)
    return connection


def fetch_all(
    connection: sqlite3.Connection,
    sql: str,
    parameters: tuple[Any, ...] = (),
) -> list[dict[str, Any]]:
    return [dict(row) for row in connection.execute(sql, parameters).fetchall()]


def fetch_one(
    connection: sqlite3.Connection,
    sql: str,
    parameters: tuple[Any, ...] = (),
) -> dict[str, Any] | None:
    rows = fetch_all(connection, sql, parameters)
    return rows[0] if rows else None


def resolve_run_lineage(connection: sqlite3.Connection) -> dict[str, str]:
    lineage: dict[str, str] = {}
    for run_name, (table_name, key_column) in RUN_TABLES.items():
        row = fetch_one(
            connection,
            f"SELECT {key_column} AS run_id FROM {table_name} ORDER BY {key_column} DESC LIMIT 1",
        )
        if row:
            lineage[run_name] = str(row["run_id"])
    return lineage


def require_lineage(lineage: dict[str, str]) -> None:
    missing = sorted(set(RUN_TABLES) - set(lineage))
    if missing:
        raise ValueError(f"Missing completed upstream evidence runs: {missing}")
