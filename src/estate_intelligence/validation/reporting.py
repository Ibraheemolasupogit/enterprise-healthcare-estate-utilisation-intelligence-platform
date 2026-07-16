"""Deterministic data-quality evidence exports."""

from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path
from typing import Any

from estate_intelligence.ingestion.writer import safe_export_dir

EXPORT_QUERIES = {
    "quality_rule_catalogue.csv": "SELECT * FROM evidence_quality_rule_catalogue ORDER BY rule_id",
    "quality_check_results.csv": "SELECT * FROM evidence_quality_check_results ORDER BY rule_id",
    "quality_record_issues.csv": (
        "SELECT * FROM evidence_quality_record_issues ORDER BY dataset, rule_id, record_identifier"
    ),
    "quality_dataset_scores.csv": "SELECT * FROM evidence_quality_dataset_scores ORDER BY dataset",
    "quality_dimension_scores.csv": (
        "SELECT * FROM evidence_quality_dimension_scores ORDER BY dataset, dimension"
    ),
    "quality_reconciliation_results.csv": (
        "SELECT * FROM evidence_quality_reconciliation_results ORDER BY dataset"
    ),
    "manual_review_queue.csv": (
        "SELECT * FROM evidence_quality_manual_review_queue ORDER BY review_id"
    ),
}


def export_quality_evidence(
    connection: sqlite3.Connection, output_dir: Path, quality_run_id: str
) -> dict[str, Path]:
    """Export quality evidence as deterministic CSV, JSON and Markdown."""

    resolved = safe_export_dir(output_dir)
    resolved.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}
    for filename, query in EXPORT_QUERIES.items():
        rows = [dict(row) for row in connection.execute(query).fetchall()]
        path = resolved / filename
        _write_csv(path, rows)
        written[filename] = path

    summary = _summary(connection, quality_run_id)
    summary_path = resolved / "quality_run_summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    written["quality_run_summary.json"] = summary_path

    defect_rows = [
        dict(row)
        for row in connection.execute(
            """
            SELECT intentional_issue_id, rule_id, dataset, record_identifier, severity,
                   failure_action, evidence_key
            FROM evidence_quality_record_issues
            WHERE intentional_issue_id IS NOT NULL
            ORDER BY intentional_issue_id, evidence_key
            """
        ).fetchall()
    ]
    defect_path = resolved / "intentional_defect_detection.csv"
    _write_csv(defect_path, defect_rows)
    written["intentional_defect_detection.csv"] = defect_path

    report_path = resolved / "data_quality_report.md"
    report_path.write_text(_markdown_report(summary), encoding="utf-8")
    written["data_quality_report.md"] = report_path
    return written


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    columns = list(rows[0]) if rows else ["empty"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _summary(connection: sqlite3.Connection, quality_run_id: str) -> dict[str, Any]:
    run = dict(
        connection.execute(
            "SELECT * FROM evidence_quality_runs WHERE quality_run_id = ?", (quality_run_id,)
        ).fetchone()
    )
    datasets = [
        dict(row)
        for row in connection.execute(
            "SELECT dataset, score, status FROM evidence_quality_dataset_scores ORDER BY dataset"
        ).fetchall()
    ]
    dimensions = [
        dict(row)
        for row in connection.execute(
            """
            SELECT dataset, dimension, score, status
            FROM evidence_quality_dimension_scores
            ORDER BY dataset, dimension
            """
        ).fetchall()
    ]
    severity = [
        dict(row)
        for row in connection.execute(
            """
            SELECT severity, COUNT(*) AS issue_count
            FROM evidence_quality_record_issues
            GROUP BY severity
            ORDER BY severity
            """
        ).fetchall()
    ]
    actions = [
        dict(row)
        for row in connection.execute(
            """
            SELECT failure_action, COUNT(*) AS issue_count
            FROM evidence_quality_record_issues
            GROUP BY failure_action
            ORDER BY failure_action
            """
        ).fetchall()
    ]
    manual_review = connection.execute(
        "SELECT COUNT(*) AS count FROM evidence_quality_manual_review_queue"
    ).fetchone()["count"]
    return {
        "run": run,
        "dataset_scores": datasets,
        "dimension_scores": dimensions,
        "issue_counts_by_severity": severity,
        "issue_counts_by_action": actions,
        "manual_review_count": manual_review,
        "downstream_readiness": (
            "Suitable to proceed to Milestone 5 analytics under configured rules "
            "with manual-review items retained as caveats."
        ),
    }


def _markdown_report(summary: dict[str, Any]) -> str:
    run = summary["run"]
    lines = [
        "# Data Quality Report",
        "",
        f"Quality run: `{run['quality_run_id']}`",
        f"Ingestion run: `{run['ingestion_run_id']}`",
        f"Overall status: `{run['overall_status']}`",
        f"Overall score: `{run['overall_score']}`",
        "",
        "## Dataset Scores",
    ]
    for row in summary["dataset_scores"]:
        lines.append(f"- {row['dataset']}: {row['score']} ({row['status']})")
    lines.extend(["", "## Manual Review", f"Open items: {summary['manual_review_count']}", ""])
    lines.extend(["## Downstream Readiness", summary["downstream_readiness"], ""])
    lines.extend(
        [
            "## Limitations",
            "No utilisation, forecasting, scenario, optimisation or "
            "recommendation logic is included.",
            "",
        ]
    )
    return "\n".join(lines)
