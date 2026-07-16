"""Display-only filter helpers."""

from __future__ import annotations

from typing import Any

import streamlit as st


def select_filter(label: str, values: list[Any], key: str) -> Any:
    options = ["", *sorted({str(value) for value in values if value not in (None, "")})]
    selected = st.selectbox(label, options, key=key)
    return selected or None
