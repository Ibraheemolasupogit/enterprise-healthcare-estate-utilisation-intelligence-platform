"""Scenario comparison dashboard page."""

from __future__ import annotations

import streamlit as st

from dashboard.components.charts import bar_chart
from dashboard.components.layout import page_header
from dashboard.components.tables import render_table

service = page_header(
    "Scenario Comparison", "How do heuristic scenarios compare without producing a recommendation?"
)
data = service.get_scenario_comparison()

st.error("No scenario is named as the implementation choice by this dashboard.")
bar_chart(data["comparison"], "scenario_id", "comparison_score", "Scenario score comparison.")
bar_chart(data["comparison"], "scenario_id", "capacity_headroom", "Capacity headroom.")
bar_chart(data["comparison"], "scenario_id", "rooms_deactivated", "Room actions.")
render_table(
    data["comparison"],
    "Scenario feasibility, confidence, demand, capacity and manual-review dependencies.",
)
render_table(data["costs"], "Descriptive cost comparison; values are not guaranteed savings.")
render_table(data["workforce"], "Workforce status by scenario.")
render_table(data["accessibility"], "Accessibility status by scenario.")
render_table(data["risks"], "Scenario risks.")
render_table(data["room_actions"], "Room actions with protected-capacity flags.")
