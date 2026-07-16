"""Common Streamlit page layout."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from dashboard.components.alerts import render_global_notice, render_warnings
from dashboard.components.provenance import reference_period, render_lineage
from dashboard.data.services import DashboardService


def get_service() -> DashboardService:
    database = Path(st.session_state.get("database_path", "data/processed/estate_intelligence.db"))
    return DashboardService(database)


def page_header(
    title: str,
    question: str,
    service: DashboardService | None = None,
    reference: str = "Milestones 1-10 completed evidence",
) -> DashboardService:
    st.title(title)
    st.subheader(question)
    render_global_notice()
    service = service or get_service()
    try:
        summary = service.validate()
    except FileNotFoundError:
        st.error(
            "The local dashboard database is missing. Run the milestone evidence pipeline first."
        )
        st.stop()
    render_warnings(summary.warnings)
    render_lineage(summary.run_lineage)
    reference_period(reference)
    st.caption("Assumptions and limitations are summarised on the Evidence and Limitations page.")
    return service
