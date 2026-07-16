# ruff: noqa: E501
"""Executive overview dashboard page."""

from __future__ import annotations

import streamlit as st

from dashboard.components.alerts import NO_RECOMMENDATION
from dashboard.components.charts import bar_chart
from dashboard.components.formatting import currency, integer, percent, status_label
from dashboard.components.layout import page_header
from dashboard.components.metrics import metric_grid
from dashboard.components.tables import render_table

service = page_header(
    "Executive Overview",
    "What does the current evidence say about estate utilisation, operational resilience and financial implications?",
)
summary = service.get_executive_summary()
financial = service.get_financial_summary()
simulation = service.get_simulation_summary()
scenario = service.get_scenario_comparison()["comparison"]
optimisation = service.get_optimisation_summary()["comparison"]
portfolio = service.get_estate_portfolio()

metric_grid(
    [
        ("Sites", summary.get("site_count"), integer),
        ("Buildings", summary.get("building_count"), integer),
        ("Quality-gated rooms", summary.get("room_count"), integer),
        (
            "Overall quality score",
            summary.get("overall_score"),
            lambda value: f"{float(value):.1f}" if value else "n/a",
        ),
        ("Booked utilisation", summary.get("overall_booked_utilisation"), percent),
        ("Actual utilisation", summary.get("overall_actual_utilisation"), percent),
        ("Effective utilisation", summary.get("overall_effective_utilisation"), percent),
        (
            "Forecast horizon",
            summary.get("forecast_horizon"),
            lambda value: f"{integer(value)} months",
        ),
        ("Scenario count", summary.get("scenario_count"), integer),
        ("Optimisation case count", summary.get("optimisation_case_count"), integer),
        ("Simulation readiness", summary.get("simulation_readiness"), status_label),
        ("Financial readiness", summary.get("financial_readiness"), status_label),
        ("Baseline recurring cost", summary.get("baseline_recurring_cost"), currency),
        ("Highest nominal NPV", summary.get("highest_nominal_npv"), currency),
        ("Risk-adjusted NPV", summary.get("highest_risk_adjusted_npv"), currency),
        ("Manual-review count", summary.get("manual_review_count"), integer),
    ]
)

st.error(NO_RECOMMENDATION)
bar_chart(portfolio, "building_id", "effective_utilisation", "Building utilisation ranking.")
render_table(scenario, "Heuristic scenario comparison summary.")
render_table(optimisation, "Optimisation comparison summary.")
render_table(simulation["resilience"], "Simulation resilience summary: failed rows remain visible.")
render_table(financial["comparison"], "Nominal versus risk-adjusted financial comparison.")
