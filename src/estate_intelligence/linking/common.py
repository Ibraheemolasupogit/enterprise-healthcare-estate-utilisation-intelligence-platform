"""Common deterministic entity-linking helpers."""

from __future__ import annotations

from difflib import SequenceMatcher

from estate_intelligence.linking.normalisation import normalise_text


def similarity(left: str, right: str) -> float:
    """Return deterministic text similarity."""

    return SequenceMatcher(None, normalise_text(left), normalise_text(right)).ratio()


def match_status(score: float) -> str:
    """Map a score to an explicit linkage status."""

    if score >= 0.85:
        return "matched"
    if score >= 0.70:
        return "manual_review"
    return "unmatched"
