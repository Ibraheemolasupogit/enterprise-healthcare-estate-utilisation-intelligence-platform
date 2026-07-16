"""Deterministic ingestion evidence export."""

from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path
from typing import Any

from estate_intelligence.utils.paths import repository_root

EXPORT_FILES = {
    "reconciliation_summary.csv": "SELECT * FROM evidence_reconciliation_summary ORDER BY dataset",
    "linkage_summary.csv": (
        "SELECT entity_type, match_method, match_status, COUNT(*) AS record_count "
        "FROM evidence_linkage_results GROUP BY entity_type, match_method, match_status "
        "ORDER BY entity_type, match_method, match_status"
    ),
    "unmatched_records.csv": (
        "SELECT * FROM evidence_unmatched_records ORDER BY dataset, record_identifier"
    ),
    "duplicate_candidates.csv": (
        "SELECT * FROM evidence_duplicate_candidates ORDER BY duplicate_group_id"
    ),
}


def safe_export_dir(path: Path) -> Path:
    """Resolve an approved evidence export directory."""

    resolved = path.expanduser().resolve()
    root = repository_root().resolve()
    approved = [
        (root / "outputs" / "ingestion").resolve(),
        (root / "outputs" / "data_quality").resolve(),
        (root / "outputs" / "utilisation").resolve(),
        (root / "outputs" / "forecasting").resolve(),
        (root / "outputs" / "scenarios").resolve(),
        (root / "outputs" / "optimisation").resolve(),
        (root / "outputs" / "simulation").resolve(),
        (root / "outputs" / "financial").resolve(),
        (root / "data" / "processed").resolve(),
        Path("/private/tmp").resolve(),
        Path("/var").resolve(),
    ]
    if not any(resolved == base or resolved.is_relative_to(base) for base in approved):
        raise ValueError(f"Refusing unsafe evidence export path: {resolved}")
    return resolved


def export_evidence(connection: sqlite3.Connection, export_dir: Path) -> dict[str, Path]:
    """Export deterministic ingestion and linkage evidence."""

    resolved = safe_export_dir(export_dir)
    resolved.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}
    for filename, query in EXPORT_FILES.items():
        rows = [dict(row) for row in connection.execute(query).fetchall()]
        path = resolved / filename
        _write_csv(path, rows)
        written[filename] = path

    manifest = _manifest(connection)
    manifest_path = resolved / "ingestion_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    written["ingestion_manifest.json"] = manifest_path

    issues = [
        dict(row)
        for row in connection.execute(
            "SELECT * FROM evidence_intentional_issue_detection ORDER BY issue_id"
        ).fetchall()
    ]
    issues_path = resolved / "intentional_issue_detection.json"
    issues_path.write_text(
        json.dumps({"issues": issues}, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    written["intentional_issue_detection.json"] = issues_path
    return written


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if rows:
        columns = list(rows[0])
    else:
        columns = ["empty"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _manifest(connection: sqlite3.Connection) -> dict[str, Any]:
    run = connection.execute(
        "SELECT * FROM evidence_ingestion_runs ORDER BY ingestion_run_id"
    ).fetchone()
    rows = [
        dict(row)
        for row in connection.execute(
            "SELECT dataset, source_rows, curated_rows, warning_rows, rejected_rows "
            "FROM evidence_reconciliation_summary ORDER BY dataset"
        ).fetchall()
    ]
    return {"ingestion_run": dict(run) if run else {}, "reconciliation": rows}
