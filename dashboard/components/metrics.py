"""Metric rendering helpers."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import streamlit as st


def metric_grid(items: list[tuple[str, Any, Callable[[Any], str]]], columns: int = 4) -> None:
    cols = st.columns(columns)
    for index, (label, value, formatter) in enumerate(items):
        cols[index % columns].metric(label, formatter(value))
