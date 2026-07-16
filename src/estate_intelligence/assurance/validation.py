"""Repository, SQL, documentation and workflow assurance checks."""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Any

import yaml

from estate_intelligence.ingestion.database import execute_sql_file


def load_yaml(path: Path) -> dict[str, Any]:
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise ValueError(f"{path} must be a YAML mapping")
    return document


def validate_yaml_files(root: Path, required_files: list[str]) -> list[str]:
    missing = [name for name in required_files if not (root / "config" / name).is_file()]
    for path in sorted((root / "config").rglob("*.yaml")):
        load_yaml(path)
    return missing


def validate_migration_order(schema_dir: Path) -> tuple[bool, str]:
    numbers = [
        int(path.name.split("_", 1)[0]) for path in sorted(schema_dir.glob("[0-9][0-9][0-9]_*.sql"))
    ]
    expected = list(range(1, len(numbers) + 1))
    return numbers == expected, f"migrations={numbers}"


def validate_clean_schema(root: Path) -> tuple[bool, str]:
    connection = sqlite3.connect(":memory:")
    try:
        for path in sorted((root / "database" / "schema").glob("*.sql")):
            execute_sql_file(connection, path)
        for path in sorted((root / "database" / "views").glob("*.sql")):
            execute_sql_file(connection, path)
        view_count = connection.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='view'"
        ).fetchone()[0]
    finally:
        connection.close()
    return True, f"clean schema and {view_count} views executed"


def validate_docs(root: Path, required_docs: list[str]) -> list[str]:
    missing = [name for name in required_docs if not (root / "docs" / name).is_file()]
    bad_placeholders: list[str] = []
    docs = [*sorted((root / "docs").glob("*.md")), root / "README.md"]
    for path in docs:
        text = path.read_text(encoding="utf-8")
        if re.search(r"\b(TODO|TBD|lorem ipsum)\b", text, flags=re.IGNORECASE):
            bad_placeholders.append(path.relative_to(root).as_posix())
    return missing + bad_placeholders


def workflow_has_no_deployment(workflow_text: str) -> bool:
    forbidden = ("deploy", "pages", "id-token: write", "contents: write", "packages: write")
    return not any(token in workflow_text.lower() for token in forbidden)
