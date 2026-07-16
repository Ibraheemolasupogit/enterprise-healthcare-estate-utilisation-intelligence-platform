# ruff: noqa: E501
"""Forecasting dashboard page."""

from __future__ import annotations

import streamlit as st

from dashboard.components.charts import line_chart
from dashboard.components.filters import select_filter
from dashboard.components.layout import page_header
from dashboard.components.tables import render_table

service = page_header(
    "Forecasting", "What demand forecasts and uncertainty intervals are available?"
)
all_data = service.get_forecast_summary()
eligibility = all_data["eligibility"]
target = select_filter("Target", [row["target"] for row in eligibility], "forecast_target")
entity_type = select_filter(
    "Entity type", [row["entity_type"] for row in eligibility], "forecast_entity"
)
eligibility_status = select_filter(
    "Eligibility", [row["eligibility_status"] for row in eligibility], "forecast_eligibility"
)
data = service.get_forecast_summary(
    {"target": target, "entity_type": entity_type, "eligibility_status": eligibility_status}
)

st.warning(
    "Forecasts use only 24 monthly observations. Room-level forecasts are not enabled. Intervals are synthetic analytical uncertainty, not clinical guarantees."
)
line_chart(data["values"], "period", "forecast_value", "Historical and forecast series values.")
render_table(data["eligibility"], "Series eligibility statuses.")
render_table(data["selections"], "Selected models and baseline wins.")
render_table(data["accuracy"], "WAPE, MAE, RMSE, bias and interval coverage.")
render_table(data["intervals"], "Forecast interval bands.")
