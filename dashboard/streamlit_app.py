"""Milestone 11 local read-only Streamlit dashboard entry point."""

from __future__ import annotations

import streamlit as st

from dashboard.components.alerts import NO_RECOMMENDATION
from dashboard.components.charts import bar_chart
from dashboard.components.formatting import currency, integer, percent
from dashboard.components.layout import page_header
from dashboard.components.metrics import metric_grid
from dashboard.components.tables import render_table

st.set_page_config(
    page_title="Estate Intelligence Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

service = page_header(
    "Estate Intelligence Dashboard",
    "What evidence is available for local stakeholder exploration?",
)
summary = service.get_executive_summary()

metric_grid(
    [
        ("Sites", summary.get("site_count"), integer),
        ("Buildings", summary.get("building_count"), integer),
        ("Quality-gated rooms", summary.get("room_count"), integer),
        (
            "Quality score",
            summary.get("overall_score"),
            lambda value: f"{float(value):.1f}" if value else "n/a",
        ),
        ("Booked utilisation", summary.get("overall_booked_utilisation"), percent),
        ("Actual utilisation", summary.get("overall_actual_utilisation"), percent),
        ("Effective utilisation", summary.get("overall_effective_utilisation"), percent),
        ("Highest nominal NPV", summary.get("highest_nominal_npv"), currency),
    ]
)

st.error(NO_RECOMMENDATION)
st.info(
    "Use the sidebar pages to inspect portfolio, operational, financial and provenance evidence."
)

portfolio = service.get_estate_portfolio()
bar_chart(
    portfolio,
    "building_id",
    "effective_utilisation",
    "Building utilisation ranking from persisted utilisation evidence.",
)
render_table(portfolio, "Portfolio evidence excerpt.", limit=25)
