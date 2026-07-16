"""Consistent display formatting for dashboard values."""

from __future__ import annotations

from typing import Any

STATUS_LABELS: dict[str, str] = {
    "pass": "Pass",
    "pass_with_warnings": "Pass with warnings",
    "review_required": "Review required",
    "fail": "Fail",
    "feasible": "Feasible",
    "feasible_with_warnings": "Feasible with warnings",
    "infeasible": "Infeasible",
    "optimal": "Optimal",
    "not_realisable_without_mitigation": "Not realisable without mitigation",
    "insufficient_evidence": "Insufficient evidence",
}


def status_label(value: Any) -> str:
    text = str(value or "insufficient_evidence")
    return STATUS_LABELS.get(text, text.replace("_", " ").title())


def percent(value: Any) -> str:
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return "n/a"


def currency(value: Any) -> str:
    try:
        return f"GBP {float(value):,.0f}"
    except (TypeError, ValueError):
        return "n/a"


def number(value: Any) -> str:
    try:
        return f"{float(value):,.1f}"
    except (TypeError, ValueError):
        return "n/a"


def integer(value: Any) -> str:
    try:
        return f"{int(float(value)):,}"
    except (TypeError, ValueError):
        return "n/a"


def hours(value: Any) -> str:
    formatted = number(value)
    return "n/a" if formatted == "n/a" else f"{formatted} hours"


def contacts(value: Any) -> str:
    formatted = integer(value)
    return "n/a" if formatted == "n/a" else f"{formatted} contacts"


def identifier(value: Any) -> str:
    return str(value or "insufficient_evidence")
