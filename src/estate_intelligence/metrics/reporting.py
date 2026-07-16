"""Deterministic utilisation evidence exports."""

from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path
from typing import Any

from estate_intelligence.ingestion.writer import safe_export_dir

EXPORT_QUERIES = {
    "analytics_population.csv": (
        "SELECT * FROM evidence_analytics_population ORDER BY dataset, record_identifier"
    ),
    "analytics_population_exclusions.csv": (
        "SELECT * FROM evidence_analytics_exclusions ORDER BY dataset, record_identifier, rule_id"
    ),
    "room_utilisation.csv": "SELECT * FROM evidence_room_utilisation ORDER BY room_id",
    "building_utilisation.csv": (
        "SELECT * FROM evidence_building_utilisation ORDER BY building_id"
    ),
    "site_utilisation.csv": "SELECT * FROM evidence_site_utilisation ORDER BY site_id",
    "service_utilisation.csv": "SELECT * FROM evidence_service_utilisation ORDER BY service_id",
    "room_service_utilisation.csv": (
        "SELECT * FROM evidence_room_service_utilisation ORDER BY room_id, service_id"
    ),
    "weekday_utilisation.csv": (
        "SELECT * FROM evidence_time_band_utilisation WHERE grain='weekday' ORDER BY grain_value"
    ),
    "time_band_utilisation.csv": (
        "SELECT * FROM evidence_time_band_utilisation WHERE grain='time_band' ORDER BY grain_value"
    ),
    "monthly_utilisation.csv": (
        "SELECT * FROM evidence_monthly_utilisation ORDER BY month, room_id"
    ),
    "persistent_underutilisation.csv": (
        "SELECT * FROM evidence_underutilisation_flags ORDER BY room_id"
    ),
    "protected_specialist_capacity.csv": (
        "SELECT * FROM evidence_underutilisation_flags "
        "WHERE protected_capacity_flag=1 ORDER BY room_id"
    ),
    "unit_cost_metrics.csv": "SELECT * FROM evidence_unit_cost_metrics ORDER BY building_id",
}

METRIC_CATALOGUE = [
    {
        "formula_id": "available_room_hours",
        "description": "available_hours_per_week * applicable_weeks",
    },
    {
        "formula_id": "booked_utilisation",
        "description": "non_cancelled_booked_hours / available_room_hours",
    },
    {
        "formula_id": "actual_occupied_utilisation",
        "description": "completed_attended_booking_hours / available_room_hours",
    },
    {
        "formula_id": "attendance_utilisation",
        "description": "actual_attendance / planned_attendance",
    },
    {
        "formula_id": "effective_clinical_utilisation",
        "description": "configured weighted bounded component score",
    },
    {
        "formula_id": "persistent_under_utilisation",
        "description": "months below threshold across configured window",
    },
    {
        "formula_id": "unit_cost",
        "description": "configured recurring operating cost / utilisation denominator",
    },
]


def export_utilisation_evidence(
    connection: sqlite3.Connection, output_dir: Path, utilisation_run_id: str
) -> dict[str, Path]:
    """Export utilisation evidence in stable formats."""

    resolved = safe_export_dir(output_dir)
    resolved.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}
    for filename, query in EXPORT_QUERIES.items():
        rows = [dict(row) for row in connection.execute(query).fetchall()]
        path = resolved / filename
        _write_csv(path, rows)
        written[filename] = path

    catalogue_path = resolved / "utilisation_metric_catalogue.csv"
    _write_csv(catalogue_path, METRIC_CATALOGUE)
    written["utilisation_metric_catalogue.csv"] = catalogue_path

    summary = utilisation_summary(connection, utilisation_run_id)
    summary_path = resolved / "utilisation_run_summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    written["utilisation_run_summary.json"] = summary_path

    report_path = resolved / "utilisation_report.md"
    report_path.write_text(_markdown_report(summary), encoding="utf-8")
    written["utilisation_report.md"] = report_path
    return written


def utilisation_summary(connection: sqlite3.Connection, utilisation_run_id: str) -> dict[str, Any]:
    """Build a summary payload for reports and verification."""

    run = dict(
        connection.execute(
            "SELECT * FROM evidence_utilisation_runs WHERE utilisation_run_id = ?",
            (utilisation_run_id,),
        ).fetchone()
    )
    population = [
        dict(row)
        for row in connection.execute(
            """
            SELECT dataset, analytical_status, COUNT(*) AS record_count
            FROM evidence_analytics_population
            GROUP BY dataset, analytical_status
            ORDER BY dataset, analytical_status
            """
        )
    ]
    exclusions = [
        dict(row)
        for row in connection.execute(
            """
            SELECT dataset, COUNT(*) AS record_count
            FROM evidence_analytics_exclusions
            GROUP BY dataset
            ORDER BY dataset
            """
        )
    ]
    estate = dict(
        connection.execute(
            """
            SELECT
                SUM(available_hours) AS available_hours,
                SUM(booked_hours) AS booked_hours,
                SUM(occupied_hours) AS occupied_hours,
                SUM(completed_contacts) AS completed_contacts,
                AVG(effective_utilisation) AS average_effective_utilisation
            FROM evidence_room_utilisation
            """
        ).fetchone()
    )
    underutilisation = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM evidence_underutilisation_flags
        WHERE persistent_flag = 1
        """
    ).fetchone()["count"]
    protected = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM evidence_underutilisation_flags
        WHERE protected_capacity_flag = 1
        """
    ).fetchone()["count"]
    return {
        "run": run,
        "population": population,
        "exclusions": exclusions,
        "estate": estate,
        "persistent_underutilisation_count": underutilisation,
        "protected_specialist_capacity_count": protected,
        "limitations": [
            "Occupancy is proxied from completed attended booking sessions.",
            "Unit costs are descriptive synthetic figures, not audited finance results.",
            "No forecasting, scenario, optimisation or recommendation logic is included.",
        ],
    }


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    columns = list(rows[0]) if rows else ["empty"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _markdown_report(summary: dict[str, Any]) -> str:
    run = summary["run"]
    estate = summary["estate"]
    lines = [
        "# Utilisation Report",
        "",
        f"Utilisation run: `{run['utilisation_run_id']}`",
        f"Ingestion run: `{run['ingestion_run_id']}`",
        f"Quality run: `{run['quality_run_id']}`",
        f"Readiness: `{run['readiness_status']}`",
        "",
        "## Estate-Wide Utilisation",
        f"- Available room hours: {estate['available_hours']}",
        f"- Booked hours: {estate['booked_hours']}",
        f"- Occupied hours: {estate['occupied_hours']}",
        f"- Completed contacts: {estate['completed_contacts']}",
        "",
        "## Caveats",
    ]
    for limitation in summary["limitations"]:
        lines.append(f"- {limitation}")
    lines.extend(
        [
            "",
            "## Milestone 6 Readiness",
            "The evidence is ready for synthetic demand-forecasting experiments "
            "with caveats retained.",
            "",
        ]
    )
    return "\n".join(lines)
