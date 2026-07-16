"""Dynamic SQLite schema creation for dataset-specific tables."""

from __future__ import annotations

import sqlite3

from estate_intelligence.ingestion.source_registry import SOURCE_DATASETS

PROVENANCE_COLUMNS = [
    "source_file_name TEXT NOT NULL",
    "source_row_number INTEGER NOT NULL",
    "ingestion_run_id TEXT NOT NULL",
    "source_checksum TEXT NOT NULL",
]


def create_dataset_tables(connection: sqlite3.Connection) -> None:
    """Create source, staging and curated dataset tables."""

    for dataset in SOURCE_DATASETS:
        source_columns = [f"{column} TEXT" for column in dataset.columns]
        staging_columns = [f"{column} TEXT" for column in dataset.columns] + [
            "record_status TEXT NOT NULL",
            "warning_reason TEXT",
            "normalised_name TEXT",
        ]
        curated_columns = [*staging_columns, "curated_record_id TEXT NOT NULL"]
        connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS source_{dataset.name} (
              {", ".join(source_columns + PROVENANCE_COLUMNS)}
            )
            """
        )
        connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS staging_{dataset.name} (
              {", ".join(staging_columns + PROVENANCE_COLUMNS)}
            )
            """
        )
        connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS curated_{dataset.name} (
              {", ".join(curated_columns + PROVENANCE_COLUMNS)},
              PRIMARY KEY (curated_record_id)
            )
            """
        )
        connection.execute(
            f"""
            CREATE INDEX IF NOT EXISTS idx_source_{dataset.name}_run
            ON source_{dataset.name}(ingestion_run_id)
            """
        )
        connection.execute(
            f"""
            CREATE INDEX IF NOT EXISTS idx_staging_{dataset.name}_status
            ON staging_{dataset.name}(record_status)
            """
        )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS curated_sites (
          site_id TEXT PRIMARY KEY,
          normalised_site_id TEXT NOT NULL,
          source_occurrence_count INTEGER NOT NULL,
          ingestion_run_id TEXT NOT NULL
        )
        """
    )


def clear_database(connection: sqlite3.Connection) -> None:
    """Delete Milestone 3 data while keeping schema definitions."""

    tables = [
        row["name"]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
    ]
    for table in sorted(tables):
        connection.execute(f"DELETE FROM {table}")
