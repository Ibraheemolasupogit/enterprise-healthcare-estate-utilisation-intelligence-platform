"""Deterministic manifest generation for portfolio assets."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from estate_intelligence.portfolio.models import PortfolioAsset


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def classify_asset(path: str) -> str:
    if path.endswith(".mmd"):
        return "diagram"
    if path.endswith(".csv"):
        return "manifest"
    if path.endswith(".json"):
        return "manifest"
    if path.startswith("handover/"):
        return "handover"
    if path.startswith("docs/"):
        return "repository_documentation"
    return "portfolio"


def build_manifest(root: Path, asset_paths: list[str], excluded: set[str]) -> list[PortfolioAsset]:
    assets: list[PortfolioAsset] = []
    for asset_path in sorted(dict.fromkeys(asset_paths)):
        if asset_path in excluded:
            continue
        absolute_path = root / asset_path
        assets.append(
            PortfolioAsset(
                path=asset_path,
                kind=classify_asset(asset_path),
                size_bytes=absolute_path.stat().st_size,
                sha256=sha256_file(absolute_path),
            )
        )
    return assets


def write_manifest(
    root: Path,
    json_path: str,
    csv_path: str,
    assets: list[PortfolioAsset],
    statuses: dict[str, str],
) -> None:
    json_target = root / json_path
    csv_target = root / csv_path
    json_target.parent.mkdir(parents=True, exist_ok=True)
    csv_target.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "contract_version": "1.0",
        "framework_version": "m14-v1",
        "checksum_algorithm": "sha256",
        "generated_by": "estate_intelligence.portfolio",
        "asset_count": len(assets),
        "statuses": statuses,
        "assets": [asset.__dict__ for asset in assets],
    }
    json_target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    with csv_target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["path", "kind", "size_bytes", "sha256"])
        writer.writeheader()
        for asset in assets:
            writer.writerow(asset.__dict__)
