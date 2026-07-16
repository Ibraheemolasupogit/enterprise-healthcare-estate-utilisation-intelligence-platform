"""Deterministic optimisation evidence exports."""

from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path
from typing import Any

from estate_intelligence.ingestion.writer import safe_export_dir

EXPORT_QUERIES = {
    "optimisation_case_catalogue.csv": (
        "SELECT * FROM evidence_optimisation_cases ORDER BY case_id"
    ),
    "optimisation_candidates.csv": (
        "SELECT * FROM evidence_optimisation_candidates ORDER BY service_id, period, target_room_id"
    ),
    "optimisation_allocations.csv": (
        "SELECT * FROM evidence_optimisation_allocations "
        "ORDER BY case_id, service_id, period, room_id"
    ),
    "optimisation_room_status.csv": (
        "SELECT * FROM evidence_optimisation_room_status ORDER BY case_id, room_id"
    ),
    "optimisation_building_status.csv": (
        "SELECT * FROM evidence_optimisation_building_status ORDER BY case_id, building_id"
    ),
    "optimisation_service_moves.csv": (
        "SELECT * FROM evidence_optimisation_service_moves "
        "ORDER BY case_id, service_id, source_site_id, target_site_id"
    ),
    "optimisation_constraints.csv": (
        "SELECT * FROM evidence_optimisation_constraints "
        "ORDER BY case_id, constraint_family, constraint_id"
    ),
    "optimisation_binding_constraints.csv": (
        "SELECT * FROM evidence_optimisation_binding_constraints "
        "ORDER BY case_id, constraint_family, constraint_id"
    ),
    "optimisation_objective_components.csv": (
        "SELECT * FROM evidence_optimisation_objective_components ORDER BY case_id, component"
    ),
    "optimisation_solver_results.csv": (
        "SELECT * FROM evidence_optimisation_solver_results ORDER BY case_id"
    ),
    "optimisation_infeasibility.csv": (
        "SELECT * FROM evidence_optimisation_infeasibility "
        "ORDER BY case_id, diagnostic_type, diagnostic_id"
    ),
    "optimisation_comparison.csv": (
        "SELECT * FROM evidence_optimisation_comparison ORDER BY objective_value, case_id"
    ),
    "optimisation_manual_review.csv": (
        "SELECT * FROM evidence_optimisation_infeasibility "
        "WHERE diagnostic_type NOT IN ('service_period_capacity_shortfall') "
        "ORDER BY case_id, diagnostic_type, diagnostic_id"
    ),
}


def export_optimisation_evidence(
    connection: sqlite3.Connection, output_dir: Path, optimisation_run_id: str
) -> dict[str, Path]:
    """Export optimisation evidence in stable files."""

    resolved = safe_export_dir(output_dir)
    resolved.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}
    for filename, query in EXPORT_QUERIES.items():
        rows = [dict(row) for row in connection.execute(query).fetchall()]
        path = resolved / filename
        _write_csv(path, rows)
        written[filename] = path
    summary = optimisation_summary(connection, optimisation_run_id)
    summary_path = resolved / "optimisation_run_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    written["optimisation_run_summary.json"] = summary_path
    report_path = resolved / "optimisation_report.md"
    report_path.write_text(_markdown_report(summary), encoding="utf-8")
    written["optimisation_report.md"] = report_path
    return written


def optimisation_summary(
    connection: sqlite3.Connection, optimisation_run_id: str
) -> dict[str, Any]:
    run = dict(
        connection.execute(
            "SELECT * FROM evidence_optimisation_runs WHERE optimisation_run_id = ?",
            (optimisation_run_id,),
        ).fetchone()
    )
    comparison = [
        dict(row)
        for row in connection.execute(
            "SELECT * FROM evidence_optimisation_comparison ORDER BY objective_value, case_id"
        )
    ]
    solver = [
        dict(row)
        for row in connection.execute(
            "SELECT * FROM evidence_optimisation_solver_results ORDER BY case_id"
        )
    ]
    components = [
        dict(row)
        for row in connection.execute(
            """
            SELECT case_id, component, component_value, unit
            FROM evidence_optimisation_objective_components
            ORDER BY case_id, component
            """
        )
    ]
    return {
        "run": run,
        "comparison": comparison,
        "solver": solver,
        "objective_components": components,
        "statement": (
            "Optimisation evidence is mathematical allocation evidence only; "
            "no implementation recommendation is made."
        ),
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
        "# Optimisation Report",
        "",
        f"Optimisation run: `{run['optimisation_run_id']}`",
        f"Scenario run: `{run['scenario_run_id']}`",
        f"Solver: `{run['solver_identity']}`",
        f"Planning-demand basis: `{run['planning_demand_basis']}`",
        "",
        "## Case Comparison",
    ]
    for row in summary["comparison"]:
        lines.append(
            f"- {row['case_id']}: {row['solver_status']}, objective "
            f"{row['objective_value']}, allocated {row['allocated_demand_hours']}, "
            f"unmet {row['unmet_demand_hours']}"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            (
                "The solver produced the lowest configured objective among the evaluated "
                "mathematical cases. No allocation is approved or recommended by this report."
            ),
            "",
            "Readiness statement: ready for Milestone 9 simulation design.",
            "",
        ]
    )
    return "\n".join(lines)
