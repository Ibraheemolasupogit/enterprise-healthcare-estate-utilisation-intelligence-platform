# ruff: noqa: E501
"""Workforce dashboard page."""

from __future__ import annotations

import streamlit as st

from dashboard.components.charts import bar_chart, line_chart
from dashboard.components.filters import select_filter
from dashboard.components.layout import page_header
from dashboard.components.tables import render_table

service = page_header(
    "Workforce", "Where does workforce capacity constrain operational resilience?"
)
all_data = service.get_workforce_metrics()
all_rows = all_data["workforce"]
service_id = select_filter("Service", [row["service_id"] for row in all_rows], "workforce_service")
site_id = select_filter("Site", [row["site_id"] for row in all_rows], "workforce_site")
staff_group = select_filter(
    "Staff group", [row["staff_group"] for row in all_rows], "workforce_group"
)
data = service.get_workforce_metrics(
    {"service_id": service_id, "site_id": site_id, "staff_group": staff_group}
)

st.error(
    "Workforce was the dominant simulated bottleneck where blocked demand and bottleneck counts are present."
)
line_chart(data["workforce"], "period", "available_fte", "Available FTE trend.")
bar_chart(data["workforce"], "service_name", "session_capacity", "Service capacity.")
render_table(
    data["workforce"],
    "Workforce planned/available FTE, absence, vacancy and remote-working evidence.",
)
render_table(
    data["simulation_bottlenecks"],
    "Simulation workforce utilisation, blocked demand and bottlenecks.",
)
