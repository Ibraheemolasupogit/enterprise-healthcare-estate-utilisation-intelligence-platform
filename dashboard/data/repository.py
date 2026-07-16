# ruff: noqa: E501
"""Read-only SQLite repository for dashboard pages and checks."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any
from urllib.parse import quote

from dashboard.data.queries import REQUIRED_EVIDENCE_TABLES, RUN_TABLES

DEFAULT_DATABASE = Path("data/processed/estate_intelligence.db")


class DashboardDataError(RuntimeError):
    """Raised when dashboard evidence cannot be read safely."""


def database_uri(database_path: Path) -> str:
    """Return a SQLite read-only URI for a local database path."""

    absolute_path = database_path.expanduser().resolve()
    return f"file:{quote(str(absolute_path))}?mode=ro"


class DashboardRepository:
    """Small read-only wrapper around SQLite evidence tables."""

    def __init__(self, database_path: Path = DEFAULT_DATABASE) -> None:
        self.database_path = database_path

    def connect(self) -> sqlite3.Connection:
        if not self.database_path.exists():
            raise FileNotFoundError(f"Dashboard database not found: {self.database_path}")
        connection = sqlite3.connect(database_uri(self.database_path), uri=True)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only = ON")
        return connection

    def fetch_all(
        self,
        sql: str,
        parameters: Sequence[Any] | Mapping[str, Any] = (),
    ) -> list[dict[str, Any]]:
        self._validate_statement(sql)
        with self.connect() as connection:
            rows = connection.execute(sql, parameters).fetchall()
        return [dict(row) for row in rows]

    def fetch_one(
        self,
        sql: str,
        parameters: Sequence[Any] | Mapping[str, Any] = (),
    ) -> dict[str, Any] | None:
        rows = self.fetch_all(sql, parameters)
        return rows[0] if rows else None

    def table_exists(self, table_name: str) -> bool:
        row = self.fetch_one(
            "SELECT name FROM sqlite_master WHERE type IN ('table','view') AND name = ?",
            (table_name,),
        )
        return row is not None

    def validate_required_tables(
        self, required_tables: Iterable[str] = REQUIRED_EVIDENCE_TABLES
    ) -> list[str]:
        return [table for table in required_tables if not self.table_exists(table)]

    def get_run_lineage(self) -> dict[str, str]:
        lineage: dict[str, str] = {}
        for run_name, (table_name, key_column) in RUN_TABLES.items():
            row = self.fetch_one(
                f"SELECT {key_column} AS run_id FROM {table_name} ORDER BY {key_column} DESC LIMIT 1"
            )
            if row:
                lineage[run_name] = str(row["run_id"])
        return lineage

    def assert_write_blocked(self) -> bool:
        with self.connect() as connection:
            try:
                connection.execute("CREATE TABLE dashboard_write_probe (id INTEGER)")
            except sqlite3.OperationalError:
                return True
        return False

    @staticmethod
    def _validate_statement(sql: str) -> None:
        statement = sql.strip().lower()
        if not statement.startswith("select") and not statement.startswith("with"):
            raise DashboardDataError("Dashboard repository only permits SELECT statements.")
        forbidden = (";", " insert ", " update ", " delete ", " drop ", " create ", " alter ")
        padded = f" {statement} "
        if any(token in padded for token in forbidden):
            raise DashboardDataError("Dashboard repository does not execute mutating SQL.")
