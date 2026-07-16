"""Deterministic forecast evidence exports."""

from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path
from typing import Any

from estate_intelligence.ingestion.writer import safe_export_dir

EXPORT_QUERIES = {
    "forecast_series.csv": "SELECT * FROM evidence_forecast_series ORDER BY series_id, period",
    "forecast_eligibility.csv": (
        "SELECT * FROM evidence_forecast_eligibility ORDER BY target, entity_type, entity_id"
    ),
    "forecast_folds.csv": "SELECT * FROM evidence_forecast_folds ORDER BY series_id, fold_number",
    "forecast_model_comparison.csv": (
        "SELECT * FROM evidence_forecast_model_results ORDER BY series_id, model_id"
    ),
    "forecast_model_failures.csv": (
        "SELECT * FROM evidence_forecast_model_failures ORDER BY series_id, model_id"
    ),
    "forecast_selections.csv": "SELECT * FROM evidence_forecast_selections ORDER BY series_id",
    "forecast_accuracy.csv": (
        "SELECT * FROM evidence_forecast_accuracy ORDER BY series_id, model_id, metric_name"
    ),
    "forecast_values.csv": "SELECT * FROM evidence_forecast_values ORDER BY series_id, period",
    "forecast_intervals.csv": (
        "SELECT * FROM evidence_forecast_intervals ORDER BY series_id, period, interval_level"
    ),
    "service_forecast_summary.csv": (
        "SELECT target, entity_id, period, forecast_value FROM evidence_forecast_values "
        "WHERE entity_type='service' ORDER BY target, entity_id, period"
    ),
    "estate_forecast_summary.csv": (
        "SELECT target, period, forecast_value FROM evidence_forecast_values "
        "WHERE entity_type='estate' ORDER BY target, period"
    ),
}

MODEL_CATALOGUE = [
    {"model_id": "naive", "description": "most recent observed value"},
    {"model_id": "seasonal_naive", "description": "same month from prior seasonal cycle"},
    {"model_id": "moving_average", "description": "configured trailing mean"},
    {"model_id": "drift", "description": "linear first-to-last drift"},
    {"model_id": "simple_exponential_smoothing", "description": "fixed-alpha SES"},
    {"model_id": "holt_linear", "description": "fixed-parameter Holt trend"},
    {"model_id": "holt_winters_additive", "description": "fixed additive seasonal smoothing"},
]


def export_forecast_evidence(
    connection: sqlite3.Connection, output_dir: Path, forecast_run_id: str
) -> dict[str, Path]:
    """Export forecasting evidence in canonical stable files."""

    resolved = safe_export_dir(output_dir)
    resolved.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}
    for filename, query in EXPORT_QUERIES.items():
        rows = [dict(row) for row in connection.execute(query).fetchall()]
        path = resolved / filename
        _write_csv(path, rows)
        written[filename] = path
    catalogue_path = resolved / "forecast_model_catalogue.csv"
    _write_csv(catalogue_path, MODEL_CATALOGUE)
    written["forecast_model_catalogue.csv"] = catalogue_path
    summary = forecast_summary(connection, forecast_run_id)
    summary_path = resolved / "forecast_run_summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    written["forecast_run_summary.json"] = summary_path
    report_path = resolved / "forecast_report.md"
    report_path.write_text(_markdown_report(summary), encoding="utf-8")
    written["forecast_report.md"] = report_path
    return written


def forecast_summary(connection: sqlite3.Connection, forecast_run_id: str) -> dict[str, Any]:
    """Build a compact forecast summary."""

    run = dict(
        connection.execute(
            "SELECT * FROM evidence_forecast_runs WHERE forecast_run_id = ?",
            (forecast_run_id,),
        ).fetchone()
    )
    eligibility = [
        dict(row)
        for row in connection.execute(
            """
            SELECT eligibility_status, COUNT(*) AS series_count
            FROM evidence_forecast_eligibility
            GROUP BY eligibility_status
            ORDER BY eligibility_status
            """
        )
    ]
    targets = [
        dict(row)
        for row in connection.execute(
            """
            SELECT target, entity_type, COUNT(DISTINCT series_id) AS series_count
            FROM evidence_forecast_series
            GROUP BY target, entity_type
            ORDER BY target, entity_type
            """
        )
    ]
    selections = [
        dict(row)
        for row in connection.execute(
            """
            SELECT selected_model_id, COUNT(*) AS series_count
            FROM evidence_forecast_selections
            GROUP BY selected_model_id
            ORDER BY selected_model_id
            """
        )
    ]
    return {
        "run": run,
        "eligibility": eligibility,
        "targets": targets,
        "selections": selections,
        "limitations": [
            "Forecasts are based on 24 synthetic monthly periods.",
            "Room-level forecasting is not enabled because room series are sparse.",
            "Forecasts are not consolidation, closure or relocation recommendations.",
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
    lines = [
        "# Forecast Report",
        "",
        f"Forecast run: `{run['forecast_run_id']}`",
        f"Ingestion run: `{run['ingestion_run_id']}`",
        f"Quality run: `{run['quality_run_id']}`",
        f"Utilisation run: `{run['utilisation_run_id']}`",
        "Historical period: "
        f"`{run['historical_start_period']}` to `{run['historical_end_period']}`",
        f"Forecast horizon: {run['forecast_horizon']} months",
        f"Readiness: `{run['readiness_status']}`",
        "",
        "## Eligibility Summary",
    ]
    for row in summary["eligibility"]:
        lines.append(f"- {row['eligibility_status']}: {row['series_count']}")
    lines.extend(["", "## Selected Models"])
    for row in summary["selections"]:
        lines.append(f"- {row['selected_model_id']}: {row['series_count']}")
    lines.extend(["", "## Caveats"])
    for limitation in summary["limitations"]:
        lines.append(f"- {limitation}")
    lines.extend(
        [
            "",
            "## Milestone 7 Readiness",
            "The demand forecasts are ready for synthetic scenario-engine inputs, "
            "subject to sparse-series caveats and local validation.",
            "",
        ]
    )
    return "\n".join(lines)
