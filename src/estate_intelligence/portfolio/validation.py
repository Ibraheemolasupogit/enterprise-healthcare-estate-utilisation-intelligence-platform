"""Validation helpers for final handover assets."""

from __future__ import annotations

import json
import re
from pathlib import Path

LOCAL_ABSOLUTE_PATH = re.compile(r"/Users/|/private/|C:\\\\")
PLACEHOLDER_MARKERS = ("TODO", "TBD", "lorem ipsum", "placeholder")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def validate_assets_exist(root: Path, assets: list[str]) -> list[str]:
    return [asset for asset in assets if not (root / asset).is_file()]


def validate_markdown_text(
    root: Path,
    assets: list[str],
    forbidden_terms: tuple[str, ...],
) -> list[str]:
    failures: list[str] = []
    for asset in assets:
        if not asset.endswith(".md"):
            continue
        path = root / asset
        text = read_text(path)
        lowered = text.lower()
        for marker in PLACEHOLDER_MARKERS:
            if marker.lower() in lowered:
                failures.append(f"{asset} contains placeholder marker {marker!r}")
        for term in forbidden_terms:
            if term.lower() in lowered:
                failures.append(f"{asset} contains forbidden term {term!r}")
        if LOCAL_ABSOLUTE_PATH.search(text):
            failures.append(f"{asset} contains a local absolute path")
        if "synthetic" not in lowered:
            failures.append(f"{asset} does not state the synthetic evidence boundary")
    return failures


def validate_diagrams(root: Path, diagrams: list[str]) -> list[str]:
    failures: list[str] = []
    for diagram in diagrams:
        text = read_text(root / diagram).strip()
        first_line = text.splitlines()[0] if text else ""
        if not first_line.startswith(("flowchart ", "graph ")):
            failures.append(f"{diagram} does not start with a Mermaid graph declaration")
        if "TODO" in text or "TBD" in text:
            failures.append(f"{diagram} contains placeholder text")
    return failures


def validate_manifest(root: Path, manifest_json: str, manifest_csv: str) -> list[str]:
    failures: list[str] = []
    json_path = root / manifest_json
    csv_path = root / manifest_csv
    if not json_path.is_file() or not csv_path.is_file():
        return ["portfolio manifest files are missing"]
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    paths = {asset["path"] for asset in payload.get("assets", [])}
    if manifest_json in paths:
        failures.append("portfolio manifest JSON checksums itself")
    if payload.get("checksum_algorithm") != "sha256":
        failures.append("portfolio manifest does not use sha256")
    if not paths:
        failures.append("portfolio manifest has no assets")
    return failures
