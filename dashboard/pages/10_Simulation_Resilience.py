# ruff: noqa: E501
"""Simulation resilience dashboard page."""

from __future__ import annotations

import streamlit as st

from dashboard.components.charts import bar_chart
from dashboard.components.layout import page_header
from dashboard.components.tables import render_table

service = page_header(
    "Simulation Resilience", "Did mathematically feasible cases remain operationally resilient?"
)
data = service.get_simulation_summary()
failed_rows = [row for row in data["resilience"] if row.get("status") == "fail"]

st.error(
    f"All {len(data['resilience'])} case/experiment resilience rows failed."
    if len(failed_rows) == len(data["resilience"])
    else "Simulation failures are present and require review."
)
st.warning(
    "Mathematical feasibility did not imply operational resilience. Results are synthetic and not clinically validated."
)
bar_chart(
    data["resilience"],
    "simulation_case_id",
    "completion_rate",
    "Completion rate by case and experiment.",
)
bar_chart(data["resilience"], "simulation_case_id", "p95_wait_minutes", "Wait-time comparison.")
bar_chart(data["resilience"], "simulation_case_id", "unserved_contacts", "Unserved demand.")
bar_chart(data["workforce"], "service_id", "workforce_utilisation", "Workforce utilisation.")
render_table(data["cases"], "Four simulation cases.")
render_table(data["experiments"], "Six simulation experiments.")
render_table(data["resilience"], "Resilience metrics and threshold status.")
render_table(data["thresholds"], "Threshold failure frequency and status.")
render_table(data["workforce"], "Workforce blocked contacts and bottleneck counts.")
