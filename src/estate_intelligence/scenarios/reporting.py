"""Deterministic scenario evidence exports."""

from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path
from typing import Any

from estate_intelligence.ingestion.writer import safe_export_dir

EXPORT_QUERIES = {
    "scenario_catalogue.csv": "SELECT * FROM evidence_scenario_catalogue ORDER BY scenario_id",
    "scenario_candidates.csv": (
        "SELECT * FROM evidence_scenario_candidates ORDER BY scenario_id, candidate_type, entity_id"
    ),
    "scenario_comparison.csv": (
        "SELECT * FROM evidence_scenario_comparison ORDER BY comparison_score DESC, scenario_id"
    ),
    "scenario_capacity.csv": (
        "SELECT * FROM evidence_scenario_capacity ORDER BY scenario_id, grain, entity_id"
    ),
    "scenario_room_actions.csv": (
        "SELECT * FROM evidence_scenario_room_actions ORDER BY scenario_id, room_id"
    ),
    "scenario_service_moves.csv": (
        "SELECT * FROM evidence_scenario_service_moves ORDER BY scenario_id, service_id"
    ),
    "scenario_compatibility.csv": (
        "SELECT * FROM evidence_scenario_compatibility ORDER BY scenario_id, service_id, room_id"
    ),
    "scenario_workforce.csv": (
        "SELECT * FROM evidence_scenario_workforce ORDER BY scenario_id, service_id, site_id"
    ),
    "scenario_accessibility.csv": (
        "SELECT * FROM evidence_scenario_accessibility ORDER BY scenario_id, site_id"
    ),
    "scenario_costs.csv": "SELECT * FROM evidence_scenario_costs ORDER BY scenario_id",
    "scenario_constraints.csv": (
        "SELECT * FROM evidence_scenario_constraints "
        "ORDER BY scenario_id, constraint_category, constraint_name"
    ),
    "scenario_risks.csv": (
        "SELECT * FROM evidence_scenario_risks ORDER BY scenario_id, risk_category"
    ),
    "scenario_scores.csv": "SELECT * FROM evidence_scenario_scores ORDER BY scenario_id, dimension",
    "scenario_manual_review.csv": (
        "SELECT * FROM evidence_scenario_constraints "
        "WHERE result_status='warning' "
        "ORDER BY scenario_id, constraint_category, constraint_name"
    ),
}


def export_scenario_evidence(
    connection: sqlite3.Connection, output_dir: Path, scenario_run_id: str
) -> dict[str, Path]:
    """Export scenario evidence in stable files."""

    resolved = safe_export_dir(output_dir)
    resolved.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}
    for filename, query in EXPORT_QUERIES.items():
        rows = [dict(row) for row in connection.execute(query).fetchall()]
        path = resolved / filename
        _write_csv(path, rows)
        written[filename] = path
    summary = scenario_summary(connection, scenario_run_id)
    summary_path = resolved / "scenario_run_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    written["scenario_run_summary.json"] = summary_path
    report_path = resolved / "scenario_report.md"
    report_path.write_text(_markdown_report(summary), encoding="utf-8")
    written["scenario_report.md"] = report_path
    return written


def scenario_summary(connection: sqlite3.Connection, scenario_run_id: str) -> dict[str, Any]:
    """Build summary payload."""

    run = dict(
        connection.execute(
            "SELECT * FROM evidence_scenario_runs WHERE scenario_run_id=?", (scenario_run_id,)
        ).fetchone()
    )
    comparison = [
        dict(row)
        for row in connection.execute(
            "SELECT * FROM evidence_scenario_comparison ORDER BY comparison_score DESC, scenario_id"
        )
    ]
    constraints = [
        dict(row)
        for row in connection.execute(
            """
            SELECT result_status, COUNT(*) AS count
            FROM evidence_scenario_constraints
            GROUP BY result_status
            ORDER BY result_status
            """
        )
    ]
    return {
        "run": run,
        "comparison": comparison,
        "constraints": constraints,
        "statement": "Scenario comparison evidence only; no implementation recommendation is made.",
    }


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    columns = list(rows[0]) if rows else ["empty"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _markdown_report(summary: dict[str, Any]) -> str:
    run = summary["run"]
    lines = [
        "# Scenario Report",
        "",
        f"Scenario run: `{run['scenario_run_id']}`",
        f"Forecast run: `{run['forecast_run_id']}`",
        f"Demand basis: `{run['demand_basis']}` / `{run['interval_basis']}`",
        "",
        "## Scenario Comparison",
    ]
    for row in summary["comparison"]:
        lines.append(
            f"- {row['scenario_id']}: {row['feasibility_status']}, "
            f"score {row['comparison_score']}, confidence {row['confidence_status']}"
        )
    lines.extend(["", "No scenario is approved or recommended by this report.", ""])
    return "\n".join(lines)
