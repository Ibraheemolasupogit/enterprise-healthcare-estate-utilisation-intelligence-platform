"""Audience catalogue helpers."""

from __future__ import annotations

from typing import Any

from estate_intelligence.reporting.models import Audience


def load_audiences(document: dict[str, Any]) -> list[Audience]:
    return [
        Audience(
            audience_id=str(row["audience_id"]),
            label=str(row["label"]),
            detail_level=str(row["detail_level"]),
            primary_need=str(row["primary_need"]),
        )
        for row in document["audience_catalogue"]
    ]
