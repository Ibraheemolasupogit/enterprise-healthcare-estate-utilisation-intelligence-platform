"""Room utilisation dashboard page."""

from __future__ import annotations

import streamlit as st

from dashboard.components.charts import bar_chart
from dashboard.components.filters import select_filter
from dashboard.components.layout import page_header
from dashboard.components.tables import render_table

service = page_header(
    "Room Utilisation", "Which rooms show utilisation, protected capacity and quality caveats?"
)
all_rows = service.get_room_utilisation()

cols = st.columns(5)
with cols[0]:
    site_id = select_filter("Site", [row["site_id"] for row in all_rows], "room_site")
with cols[1]:
    building_id = select_filter(
        "Building", [row["building_id"] for row in all_rows], "room_building"
    )
with cols[2]:
    room_type = select_filter("Room type", [row["room_type"] for row in all_rows], "room_type")
with cols[3]:
    protected = select_filter(
        "Protected", [row["protected_capacity_flag"] for row in all_rows], "room_protected"
    )
with cols[4]:
    persistent = select_filter(
        "Persistent underuse", [row["persistent_flag"] for row in all_rows], "room_persistent"
    )

rows = service.get_room_utilisation(
    {
        "site_id": site_id,
        "building_id": building_id,
        "room_type": room_type,
        "protected_capacity_flag": protected,
        "persistent_flag": persistent,
    }
)
st.info(
    "Protected specialist rooms are not labelled inefficient solely because utilisation is low."
)
bar_chart(rows, "room_id", "effective_utilisation", "Room-utilisation distribution.")
bar_chart(rows, "room_id", "booked_utilisation", "Booked utilisation by room.")
render_table(rows, "Room utilisation, availability, contacts and protected-capacity evidence.")
