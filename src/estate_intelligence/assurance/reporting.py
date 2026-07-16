"""Assurance report rendering."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from estate_intelligence.assurance.reproducibility import stable_json


def write_json(path: Path, data: Any) -> None:
    path.write_text(stable_json(data), encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_markdown_report(path: Path, title: str, sections: list[tuple[str, str]]) -> None:
    lines = [f"# {title}", ""]
    for heading, body in sections:
        lines.extend([f"## {heading}", "", body, ""])
    path.write_text("\n".join(lines), encoding="utf-8")
