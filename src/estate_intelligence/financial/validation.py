"""Financial validation helpers."""

from __future__ import annotations


def require_rows(name: str, count: int) -> None:
    if count <= 0:
        raise ValueError(f"Required financial evidence source has no rows: {name}")
