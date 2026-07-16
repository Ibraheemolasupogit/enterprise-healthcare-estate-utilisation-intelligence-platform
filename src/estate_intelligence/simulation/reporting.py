"""Deterministic simulation evidence exports."""

from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path
from typing import Any

from estate_intelligence.ingestion.writer import safe_export_dir

EXPORT_QUERIES = {
    "simulation_case_catalogue.csv": (
        "SELECT * FROM evidence_simulation_cases ORDER BY simulation_case_id"
    ),
    "simulation_experiment_catalogue.csv": (
        "SELECT * FROM evidence_simulation_experiments ORDER BY experiment_id"
    ),
    "simulation_replications.csv": (
        "SELECT * FROM evidence_simulation_replications "
        "ORDER BY simulation_case_id, experiment_id, replication"
    ),
    "simulation_service_metrics.csv": (
        "SELECT * FROM evidence_simulation_service_metrics "
        "ORDER BY simulation_case_id, experiment_id, service_id"
    ),
    "simulation_resource_metrics.csv": (
        "SELECT * FROM evidence_simulation_resource_metrics "
        "ORDER BY simulation_case_id, experiment_id, room_id"
    ),
    "simulation_queue_metrics.csv": (
        "SELECT * FROM evidence_simulation_queue_metrics "
        "ORDER BY simulation_case_id, experiment_id, service_id, room_id"
    ),
    "simulation_workforce_metrics.csv": (
        "SELECT * FROM evidence_simulation_workforce_metrics "
        "ORDER BY simulation_case_id, experiment_id, service_id"
    ),
    "simulation_resilience_metrics.csv": (
        "SELECT * FROM evidence_simulation_resilience_metrics "
        "ORDER BY simulation_case_id, experiment_id"
    ),
    "simulation_threshold_results.csv": (
        "SELECT * FROM evidence_simulation_threshold_results "
        "ORDER BY simulation_case_id, experiment_id, threshold_name"
    ),
    "simulation_failures.csv": (
        "SELECT * FROM evidence_simulation_failures "
        "ORDER BY simulation_case_id, experiment_id, failure_id"
    ),
    "simulation_comparison.csv": (
        "SELECT * FROM evidence_simulation_summary "
        "ORDER BY status DESC, simulation_case_id, experiment_id"
    ),
    "simulation_event_sample.csv": (
        "SELECT * FROM evidence_simulation_events "
        "ORDER BY simulation_case_id, experiment_id, replication, event_sequence"
    ),
}


def export_simulation_evidence(
    connection: sqlite3.Connection, output_dir: Path, simulation_run_id: str
) -> dict[str, Path]:
    """Export simulation evidence in stable files."""

    resolved = safe_export_dir(output_dir)
    resolved.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}
    for filename, query in EXPORT_QUERIES.items():
        rows = [dict(row) for row in connection.execute(query).fetchall()]
        path = resolved / filename
        _write_csv(path, rows)
        written[filename] = path
    summary = simulation_summary(connection, simulation_run_id)
    summary_path = resolved / "simulation_run_summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    written["simulation_run_summary.json"] = summary_path
    report_path = resolved / "simulation_report.md"
    report_path.write_text(_markdown_report(summary), encoding="utf-8")
    written["simulation_report.md"] = report_path
    return written


def simulation_summary(connection: sqlite3.Connection, simulation_run_id: str) -> dict[str, Any]:
    run = dict(
        connection.execute(
            "SELECT * FROM evidence_simulation_runs WHERE simulation_run_id = ?",
            (simulation_run_id,),
        ).fetchone()
    )
    cases = [
        dict(row)
        for row in connection.execute(
            "SELECT * FROM evidence_simulation_cases ORDER BY simulation_case_id"
        )
    ]
    experiments = [
        dict(row)
        for row in connection.execute(
            "SELECT * FROM evidence_simulation_experiments ORDER BY experiment_id"
        )
    ]
    comparison = [
        dict(row)
        for row in connection.execute(
            "SELECT * FROM evidence_simulation_summary ORDER BY simulation_case_id, experiment_id"
        )
    ]
    thresholds = [
        dict(row)
        for row in connection.execute(
            "SELECT * FROM evidence_simulation_threshold_results "
            "ORDER BY simulation_case_id, experiment_id, threshold_name"
        )
    ]
    return {
        "run": run,
        "cases": cases,
        "experiments": experiments,
        "comparison": comparison,
        "thresholds": thresholds,
        "statement": (
            "Simulation evidence tests operational resilience only; no final estate "
            "recommendation or financial appraisal is made."
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
        "# Simulation Report",
        "",
        f"Simulation run: `{run['simulation_run_id']}`",
        f"Optimisation run: `{run['optimisation_run_id']}`",
        f"Scenario run: `{run['scenario_run_id']}`",
        f"Engine: `{run['simulation_engine_identity']}`",
        f"Seed strategy: `{run['seed_strategy_version']}`",
        f"Master seed: `{run['master_seed']}`",
        f"Replications: `{run['replications']}`",
        f"Time unit: `{run['time_unit']}`",
        "",
        "## Cases",
    ]
    for case in summary["cases"]:
        lines.append(
            f"- {case['simulation_case_id']}: {case['label']} ({case['active_rooms']} active rooms)"
        )
    lines.extend(["", "## Experiments"])
    for experiment in summary["experiments"]:
        lines.append(
            f"- {experiment['experiment_id']}: demand x{experiment['demand_multiplier']}, "
            f"workforce x{experiment['workforce_multiplier']}, "
            f"duration x{experiment['duration_multiplier']}"
        )
    lines.extend(["", "## Results"])
    for row in summary["comparison"]:
        lines.append(
            f"- {row['simulation_case_id']} / {row['experiment_id']}: {row['status']}, "
            f"completion {row['completion_rate']}, mean wait {row['mean_wait_minutes']}, "
            f"p95 wait {row['p95_wait_minutes']}, unserved {row['unserved_contacts']}"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            (
                "The simulation evaluates operational resilience under configured synthetic "
                "assumptions. It does not approve an allocation, calculate payback or NPV, "
                "or make a final estate recommendation."
            ),
            "",
            "Readiness statement: ready for Milestone 10 financial and sensitivity analysis.",
            "",
        ]
    )
    return "\n".join(lines)
