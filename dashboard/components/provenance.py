"""Evidence provenance display helpers."""

from __future__ import annotations

import streamlit as st


def render_lineage(lineage: dict[str, str]) -> None:
    st.caption("Current evidence run identifiers resolved from SQLite")
    st.json(lineage, expanded=False)


def reference_period(text: str) -> None:
    st.caption(f"Data last-derived reference period: {text}")
