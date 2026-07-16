"""Thin wrappers around Streamlit-native charts."""

from __future__ import annotations

from typing import Any

import streamlit as st


def bar_chart(rows: list[dict[str, Any]], x: str, y: str, caption: str) -> None:
    st.caption(caption)
    if not rows:
        st.info("No chart data is available.")
        return
    st.bar_chart(rows, x=x, y=y)


def line_chart(rows: list[dict[str, Any]], x: str, y: str, caption: str) -> None:
    st.caption(caption)
    if not rows:
        st.info("No chart data is available.")
        return
    st.line_chart(rows, x=x, y=y)
