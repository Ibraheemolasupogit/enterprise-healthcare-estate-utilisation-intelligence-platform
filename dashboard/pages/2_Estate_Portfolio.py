# ruff: noqa: E501
"""Estate portfolio dashboard page."""

from __future__ import annotations

import streamlit as st

from dashboard.components.charts import bar_chart
from dashboard.components.filters import select_filter
from dashboard.components.layout import page_header
from dashboard.components.tables import render_table

service = page_header(
    "Estate Portfolio", "How is the synthetic estate portfolio composed and used?"
)
all_rows = service.get_estate_portfolio()

cols = st.columns(4)
with cols[0]:
    site_id = select_filter("Site", [row["site_id"] for row in all_rows], "portfolio_site")
with cols[1]:
    ownership_type = select_filter(
        "Ownership", [row["ownership_type"] for row in all_rows], "portfolio_ownership"
    )
with cols[2]:
    building_type = select_filter(
        "Building type", [row["building_type"] for row in all_rows], "portfolio_type"
    )
with cols[3]:
    active_flag = select_filter(
        "Active status", [row["active_flag"] for row in all_rows], "portfolio_active"
    )

rows = service.get_estate_portfolio(
    {
        "site_id": site_id,
        "ownership_type": ownership_type,
        "building_type": building_type,
        "active_flag": active_flag,
    }
)
st.warning(
    "Buildings are not classified as closable. Optimisation labels only identify potentially releasable mathematical cases where evidence supports that wording."
)
bar_chart(rows, "building_id", "annual_operating_cost", "Building operating cost.")
bar_chart(rows, "building_id", "room_count", "Room count by building.")
render_table(rows, "Portfolio table with ownership, cost, utilisation and lease fields.")
