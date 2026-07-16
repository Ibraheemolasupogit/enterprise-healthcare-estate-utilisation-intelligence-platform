"""Milestone 3 schema checks."""

from __future__ import annotations

import sqlite3


def table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    """Return whether a table exists."""

    row = connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,)
    ).fetchone()
    return row is not None
