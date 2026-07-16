"""Deterministic financial evidence exports."""

from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path
from typing import Any

from estate_intelligence.ingestion.writer import safe_export_dir

EXPORT_QUERIES = {
    "financial_case_catalogue.csv": (
        "SELECT * FROM evidence_financial_case_catalogue ORDER BY financial_case_id"
    ),
    "financial_assumptions.csv": (
        "SELECT * FROM evidence_financial_assumptions ORDER BY assumption_set, assumption_name"
    ),
    "financial_recurring_costs.csv": (
        "SELECT * FROM evidence_financial_recurring_costs "
        "ORDER BY financial_case_id, cost_component"
    ),
    "financial_transition_costs.csv": (
        "SELECT * FROM evidence_financial_transition_costs "
        "ORDER BY financial_case_id, cost_component"
    ),
    "financial_mitigation_costs.csv": (
        "SELECT * FROM evidence_financial_mitigation_costs "
        "ORDER BY financial_case_id, cost_component"
    ),
    "financial_cashflows.csv": (
        "SELECT * FROM evidence_financial_cashflows "
        "ORDER BY financial_case_id, assumption_set, analysis_year"
    ),
    "financial_payback.csv": (
        "SELECT * FROM evidence_financial_payback ORDER BY financial_case_id, assumption_set"
    ),
    "financial_npv.csv": (
        "SELECT * FROM evidence_financial_npv ORDER BY financial_case_id, assumption_set"
    ),
    "financial_cumulative_effects.csv": (
        "SELECT * FROM evidence_financial_cumulative_effects "
        "ORDER BY financial_case_id, assumption_set"
    ),
    "financial_sensitivity.csv": (
        "SELECT * FROM evidence_financial_sensitivity "
        "ORDER BY financial_case_id, sensitivity_parameter, sensitivity_level"
    ),
    "financial_break_even.csv": (
        "SELECT * FROM evidence_financial_break_even ORDER BY financial_case_id, break_even_metric"
    ),
    "financial_risk_adjustments.csv": (
        "SELECT * FROM evidence_financial_risk_adjustments ORDER BY financial_case_id, factor_name"
    ),
    "financial_confidence.csv": (
        "SELECT * FROM evidence_financial_confidence ORDER BY financial_case_id"
    ),
    "financial_comparison.csv": (
        "SELECT * FROM evidence_financial_comparison ORDER BY financial_case_id, assumption_set"
    ),
}


def export_financial_evidence(
    connection: sqlite3.Connection, output_dir: Path, financial_run_id: str
) -> dict[str, Path]:
    resolved = safe_export_dir(output_dir)
    resolved.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}
    for filename, query in EXPORT_QUERIES.items():
        rows = [dict(row) for row in connection.execute(query).fetchall()]
        path = resolved / filename
        _write_csv(path, rows)
        written[filename] = path
    tornado_rows = _tornado_export_rows(connection)
    tornado_path = resolved / "financial_tornado_data.csv"
    _write_csv(tornado_path, tornado_rows)
    written["financial_tornado_data.csv"] = tornado_path
    summary = financial_summary(connection, financial_run_id)
    summary_path = resolved / "financial_run_summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    written["financial_run_summary.json"] = summary_path
    report_path = resolved / "financial_report.md"
    report_path.write_text(_markdown_report(summary), encoding="utf-8")
    written["financial_report.md"] = report_path
    return written


def financial_summary(connection: sqlite3.Connection, financial_run_id: str) -> dict[str, Any]:
    run = dict(
        connection.execute(
            "SELECT * FROM evidence_financial_runs WHERE financial_run_id = ?",
            (financial_run_id,),
        ).fetchone()
    )
    cases = [
        dict(row)
        for row in connection.execute(
            "SELECT * FROM evidence_financial_case_catalogue ORDER BY financial_case_id"
        )
    ]
    comparison = [
        dict(row)
        for row in connection.execute(
            "SELECT * FROM evidence_financial_comparison "
            "WHERE assumption_set = 'base' ORDER BY financial_case_id"
        )
    ]
    payback = [
        dict(row)
        for row in connection.execute(
            "SELECT * FROM evidence_financial_payback "
            "WHERE assumption_set = 'base' ORDER BY financial_case_id"
        )
    ]
    sensitivity = _tornado_export_rows(connection)[:10]
    return {
        "run": run,
        "cases": cases,
        "base_comparison": comparison,
        "base_payback": payback,
        "top_sensitivity": sensitivity,
        "statement": (
            "Financial evidence is synthetic, non-audited decision-support evidence. "
            "It is not an estate approval, guaranteed saving, or final recommendation."
        ),
    }


def _tornado_export_rows(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    return [
        dict(row)
        for row in connection.execute(
            """
            SELECT financial_case_id, sensitivity_parameter,
                   MAX(tornado_impact) AS maximum_absolute_npv_impact
            FROM evidence_financial_sensitivity
            GROUP BY financial_case_id, sensitivity_parameter
            ORDER BY maximum_absolute_npv_impact DESC, financial_case_id, sensitivity_parameter
            """
        )
    ]


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    columns = list(rows[0]) if rows else ["empty"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _markdown_report(summary: dict[str, Any]) -> str:
    run = summary["run"]
    lines = [
        "# Financial Analysis Report",
        "",
        f"Financial run: `{run['financial_run_id']}`",
        f"Simulation run: `{run['simulation_run_id']}`",
        f"Optimisation run: `{run['optimisation_run_id']}`",
        f"Scenario run: `{run['scenario_run_id']}`",
        f"Currency: `{run['currency']}`",
        f"Price basis: {run['price_basis']}",
        f"Analysis horizon: {run['analysis_horizon_years']} years",
        f"Discount rate: {run['discount_rate']}",
        f"Annual cost escalation: {run['annual_cost_escalation']}",
        "",
        "## Case Definitions",
    ]
    for case in summary["cases"]:
        lines.append(
            f"- {case['financial_case_id']}: {case['label']} "
            f"({case['source_type']} `{case['source_case_id']}`)"
        )
    lines.extend(["", "## Base Results"])
    for row in summary["base_comparison"]:
        lines.append(
            f"- {row['financial_case_id']}: NPV {row['npv']}, "
            f"risk-adjusted NPV {row['risk_adjusted_npv']}, "
            f"five-year cumulative effect {row['five_year_cumulative_effect']}, "
            f"readiness `{row['readiness_status']}`."
        )
    lines.extend(["", "## Sensitivity Ranking"])
    for row in summary["top_sensitivity"]:
        lines.append(
            f"- {row['financial_case_id']} / {row['sensitivity_parameter']}: "
            f"{row['maximum_absolute_npv_impact']}"
        )
    lines.extend(
        [
            "",
            "## Operational Resilience Dependency",
            "",
            (
                "Options linked to failed simulation thresholds retain nominal financial "
                "calculations for comparison, but are not treated as financially realisable "
                "without operational remediation and configured mitigation costs."
            ),
            "",
            "## Boundary",
            "",
            (
                "This report uses synthetic, non-audited planning assumptions. It does not "
                "approve any estate change, guarantee savings, or make a final implementation "
                "recommendation."
            ),
            "",
            "Readiness statement: ready for Milestone 11 dashboard and stakeholder views.",
            "",
        ]
    )
    return "\n".join(lines)
