"""SQLite database helpers for the local curated database."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import yaml

from estate_intelligence.utils.paths import repository_root


def load_database_path(config_path: Path | None = None) -> Path:
    """Load the configured SQLite database path."""

    path = config_path or repository_root() / "config" / "database.yaml"
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise ValueError("database configuration must be a mapping")
    database = document["database"]
    return Path(str(database["path"]))


def safe_database_path(path: Path) -> Path:
    """Resolve and validate an approved local SQLite database path."""

    resolved = path.expanduser().resolve()
    root = repository_root().resolve()
    approved = [
        (root / "data" / "processed").resolve(),
        Path("/private/tmp").resolve(),
        Path("/var").resolve(),
    ]
    if not any(resolved == base or resolved.is_relative_to(base) for base in approved):
        raise ValueError(f"Refusing unsafe database path: {resolved}")
    if resolved.suffix not in {".db", ".sqlite", ".sqlite3"}:
        raise ValueError("SQLite database path must use .db, .sqlite or .sqlite3")
    return resolved


def connect(database_path: Path) -> sqlite3.Connection:
    """Open a SQLite connection with local safety pragmas."""

    resolved = safe_database_path(database_path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(resolved)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    connection.execute("PRAGMA journal_mode = WAL")
    return connection


def execute_sql_file(connection: sqlite3.Connection, sql_path: Path) -> None:
    """Execute a SQLite SQL asset."""

    connection.executescript(sql_path.read_text(encoding="utf-8"))


def initialise_schema(connection: sqlite3.Connection) -> None:
    """Initialise all Milestone 3 tables, indexes and views."""

    root = repository_root()
    for path in sorted((root / "database" / "schema").glob("*.sql")):
        execute_sql_file(connection, path)
    for path in sorted((root / "database" / "views").glob("*.sql")):
        execute_sql_file(connection, path)
