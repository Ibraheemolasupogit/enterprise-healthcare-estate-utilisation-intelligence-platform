"""Evidence and limitations dashboard page."""

from __future__ import annotations

import streamlit as st

from dashboard.components.layout import page_header
from dashboard.components.tables import render_table

service = page_header(
    "Evidence and Limitations",
    "What provenance, assumptions and boundaries should users keep visible?",
)
data = service.get_limitations()

st.subheader("Run Lineage")
st.json(data["lineage"], expanded=True)
render_table(data["row_counts"], "Evidence row counts by table.")
st.subheader("Boundaries")
for boundary in data["boundaries"]:
    st.warning(boundary)
st.markdown(
    """
    Repository documentation references:

    - docs/dashboard_architecture.md
    - docs/dashboard_pages.md
    - docs/dashboard_data_access.md
    - docs/dashboard_interpretation.md
    - docs/dashboard_operations.md
    - docs/limitations.md
    - docs/simulation_resilience.md
    - docs/financial_methodology.md
    """
)
