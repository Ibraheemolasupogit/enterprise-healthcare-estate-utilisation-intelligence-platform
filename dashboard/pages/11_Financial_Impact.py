# ruff: noqa: E501
"""Financial impact dashboard page."""

from __future__ import annotations

import streamlit as st

from dashboard.components.charts import bar_chart, line_chart
from dashboard.components.layout import page_header
from dashboard.components.tables import render_table

service = page_header(
    "Financial Impact", "What nominal financial effects exist and why are they not realisable yet?"
)
data = service.get_financial_summary()

st.error("All cases are not realisable without mitigation under the current simulation evidence.")
st.warning(
    "Case E and Case G are not presented as implementation choices merely because nominal NPV is positive."
)
bar_chart(data["comparison"], "financial_case_id", "npv", "Nominal NPV.")
bar_chart(data["comparison"], "financial_case_id", "risk_adjusted_npv", "Risk-adjusted NPV.")
line_chart(data["cashflows"], "analysis_year", "net_annual_financial_effect", "Annual cash flow.")
line_chart(data["cashflows"], "analysis_year", "cumulative_cash_flow", "Cumulative cash flow.")
bar_chart(
    data["sensitivity"], "sensitivity_parameter", "tornado_impact", "Sensitivity/tornado data."
)
bar_chart(data["transition_costs"], "cost_component", "amount", "Transition-cost composition.")
render_table(data["cases"], "Seven financial cases.")
render_table(data["comparison"], "Baseline, case cost, NPV, payback, readiness and confidence.")
render_table(data["cumulative"], "Three-year and five-year effects.")
render_table(data["sensitivity"], "Optimistic/base/pessimistic sensitivity rows.")
render_table(data["break_even"], "Break-even thresholds.")
render_table(data["confidence"], "Non-realisability confidence evidence.")
