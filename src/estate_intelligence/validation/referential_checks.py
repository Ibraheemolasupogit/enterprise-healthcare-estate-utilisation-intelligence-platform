"""Focused Milestone 3 referential checks."""

from __future__ import annotations

import sqlite3


def count_missing_references(
    connection: sqlite3.Connection,
    table: str,
    column: str,
    reference_table: str,
    reference_column: str,
) -> int:
    """Count missing references for a simple key relationship."""

    row = connection.execute(
        f"""
        SELECT COUNT(*) AS count
        FROM {table} source
        LEFT JOIN {reference_table} reference ON source.{column} = reference.{reference_column}
        WHERE reference.{reference_column} IS NULL
        """
    ).fetchone()
    return int(row["count"])
