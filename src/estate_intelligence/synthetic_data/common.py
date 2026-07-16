"""Common deterministic serialization helpers for synthetic source data."""

from __future__ import annotations

import csv
import hashlib
import json
import tempfile
from collections.abc import Iterable, Mapping, Sequence
from datetime import date, time
from decimal import Decimal
from pathlib import Path
from typing import Any

from estate_intelligence.utils.paths import repository_root

CSVValue = str | int | float | bool | date | time | Decimal | None
CSVRow = Mapping[str, CSVValue]


def canonical_value(value: CSVValue) -> str:
    """Convert supported values to deterministic CSV strings."""

    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, time):
        return value.strftime("%H:%M")
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, float):
        return f"{value:.4f}".rstrip("0").rstrip(".")
    return str(value)


def sha256_file(path: Path) -> str:
    """Return the SHA-256 checksum for a file."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_output_dir(output_dir: Path) -> Path:
    """Resolve and validate an approved synthetic-data output directory."""

    resolved = output_dir.expanduser().resolve()
    root = repository_root().resolve()
    approved_roots = [
        root / "data",
        Path(tempfile.gettempdir()).resolve(),
        Path("/private/tmp").resolve(),
        Path("/private/var").resolve(),
    ]
    if not any(
        resolved == approved or resolved.is_relative_to(approved) for approved in approved_roots
    ):
        msg = f"Refusing to generate synthetic data outside approved directories: {resolved}"
        raise ValueError(msg)
    return resolved


def atomic_write_csv(
    path: Path,
    rows: Sequence[CSVRow],
    columns: Sequence[str],
    *,
    overwrite: bool,
) -> None:
    """Write deterministic CSV using fixed columns and LF line endings."""

    if path.exists() and not overwrite:
        raise FileExistsError(f"Refusing to overwrite existing file without --overwrite: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f".{path.name}.tmp")
    with temp_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(columns), lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: canonical_value(row.get(column)) for column in columns})
    temp_path.replace(path)


def atomic_write_json(path: Path, payload: Mapping[str, Any], *, overwrite: bool) -> None:
    """Write deterministic JSON with stable ordering."""

    if path.exists() and not overwrite:
        raise FileExistsError(f"Refusing to overwrite existing file without --overwrite: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f".{path.name}.tmp")
    temp_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    temp_path.replace(path)


def sorted_rows(rows: Iterable[CSVRow], key: str) -> list[CSVRow]:
    """Sort rows by a stable identifier key."""

    return sorted(rows, key=lambda row: str(row[key]))
