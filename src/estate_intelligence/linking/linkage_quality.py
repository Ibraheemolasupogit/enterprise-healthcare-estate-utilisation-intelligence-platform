"""Linkage-quality metrics for Milestone 3."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


def summarise_linkage(results: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    """Summarise linkage outcomes."""

    summary = {
        "total": 0,
        "exact_matches": 0,
        "composite_matches": 0,
        "normalised_matches": 0,
        "warning_matches": 0,
        "manual_review_records": 0,
        "unmatched_records": 0,
    }
    for result in results:
        summary["total"] += 1
        method = str(result["match_method"])
        status = str(result["match_status"])
        if method == "exact_identifier":
            summary["exact_matches"] += 1
        elif method == "composite_key":
            summary["composite_matches"] += 1
        elif method == "normalised_name":
            summary["normalised_matches"] += 1
        if status == "matched_with_warning":
            summary["warning_matches"] += 1
        elif status == "manual_review":
            summary["manual_review_records"] += 1
        elif status == "unmatched":
            summary["unmatched_records"] += 1
    return summary
