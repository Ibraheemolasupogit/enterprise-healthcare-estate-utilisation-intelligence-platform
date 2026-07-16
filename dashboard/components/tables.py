"""Table rendering helpers."""

from __future__ import annotations

from typing import Any

import streamlit as st


def render_table(rows: list[dict[str, Any]], caption: str, limit: int = 100) -> None:
    st.caption(caption)
    if not rows:
        st.info("No evidence rows are available for this view.")
        return
    st.dataframe(rows[:limit], width="stretch", hide_index=True)
    if len(rows) > limit:
        st.caption(f"Showing {limit} of {len(rows)} rows.")
