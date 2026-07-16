"""Accessible dashboard warning and status copy."""

from __future__ import annotations

from typing import Any

import streamlit as st

GLOBAL_NOTICE = (
    "Synthetic demonstration only\n\n"
    "No real patient or estate data\n\n"
    "No estate decision is approved by this application"
)

NO_RECOMMENDATION = (
    "No implementation recommendation is made. Positive nominal NPV does not override "
    "failed simulation resilience or unresolved mitigation."
)


def render_global_notice() -> None:
    st.warning(GLOBAL_NOTICE)


def render_warnings(warnings: list[str] | tuple[str, ...]) -> None:
    for warning in warnings:
        st.error(warning) if "not_realisable" in warning else st.warning(warning)


def render_status_banner(message: str, status: Any = "review_required") -> None:
    text = f"{str(status).replace('_', ' ').title()}: {message}"
    if status in {"fail", "not_realisable_without_mitigation", "review_required"}:
        st.error(text)
    elif status in {"pass_with_warnings", "feasible_with_warnings"}:
        st.warning(text)
    else:
        st.info(text)
