"""Communication and decision-record dashboard page."""

from __future__ import annotations

import streamlit as st

from dashboard.components.layout import page_header
from dashboard.components.tables import render_table

service = page_header(
    "Communication and Decision Record",
    "How are synthetic evidence, challenges and non-approving governance options documented?",
)
data = service.get_communication_summary()

st.warning(
    "Communication evidence is synthetic and non-approving. No final recommendation, "
    "approval workflow or stakeholder agreement is represented."
)

render_table(data["runs"], "Communication run and decision status.")
render_table(data["options"], "Option catalogue. Every implementation status remains not_approved.")
render_table(data["objections"], "Synthetic stakeholder objection register.")
render_table(data["challenges"], "Evidence-based challenge responses.")
render_table(data["revisions"], "Analytical interpretation revision history.")
render_table(data["claims"], "Claim-to-evidence lineage.")
render_table(data["decision_records"], "Governance-ready decision record.")
