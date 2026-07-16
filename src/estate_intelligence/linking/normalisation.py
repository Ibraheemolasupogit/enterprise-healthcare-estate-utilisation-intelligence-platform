"""Deterministic text normalisation for entity linking."""

from __future__ import annotations

import re
import unicodedata


def normalise_text(value: str | None, *, remove_suffixes: bool = False) -> str:
    """Normalise text conservatively for deterministic comparison."""

    if value is None:
        return ""
    text = unicodedata.normalize("NFKC", value)
    text = text.strip().lower()
    text = (
        text.replace("\u2019", "'")
        .replace("\u2010", "-")
        .replace("\u2013", "-")
        .replace("\u2014", "-")
    )
    text = re.sub(r"[^\w\s#'-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if remove_suffixes:
        text = re.sub(r"\b(centre|center|clinic|building|house|wing|rooms)\b$", "", text).strip()
    return text
