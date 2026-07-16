"""Optimisation dashboard page."""

from __future__ import annotations

import streamlit as st

from dashboard.components.charts import bar_chart
from dashboard.components.layout import page_header
from dashboard.components.tables import render_table

service = page_header(
    "Optimisation", "What mathematical allocations were produced and where are their limits?"
)
data = service.get_optimisation_summary()

st.error("Mathematical optimality is not operational approval.")
bar_chart(data["comparison"], "case_id", "objective_value", "Objective values.")
bar_chart(data["comparison"], "case_id", "inactive_rooms", "Active versus inactive rooms.")
render_table(
    (data["run"] and [data["run"]]) or [], "Solver identity and optimisation run metadata."
)
render_table(data["cases"], "Optimisation case statuses and configuration.")
render_table(
    data["comparison"],
    "Demand allocation, unmet demand, active rooms and potentially releasable buildings.",
)
render_table(data["objective"], "Objective component decomposition.")
render_table(data["constraints"], "Binding constraints and diagnostics.")
render_table(
    data["building_status"],
    "Building activity status; potentially releasable means mathematical case evidence only.",
)
render_table(data["allocations"], "Allocations by service and room.")
