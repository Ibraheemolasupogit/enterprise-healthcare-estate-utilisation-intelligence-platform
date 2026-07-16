"""Milestone 14 portfolio and handover service functions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from estate_intelligence.portfolio.manifest import build_manifest, write_manifest
from estate_intelligence.portfolio.models import PortfolioConfig, ValidationResult
from estate_intelligence.portfolio.validation import (
    validate_assets_exist,
    validate_diagrams,
    validate_manifest,
    validate_markdown_text,
)

ROOT = Path(__file__).resolve().parents[3]


def load_portfolio_config(config_path: Path = Path("config/portfolio.yaml")) -> PortfolioConfig:
    resolved = config_path if config_path.is_absolute() else ROOT / config_path
    document = yaml.safe_load(resolved.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise ValueError(f"Invalid portfolio config: {resolved}")
    manifest_settings = document["manifest_settings"]
    language_controls = document["language_controls"]
    return PortfolioConfig(
        path=resolved,
        required_statuses=dict(document["required_statuses"]),
        portfolio_assets=tuple(document["required_portfolio_assets"]),
        handover_assets=tuple(document["required_handover_assets"]),
        diagrams=tuple(document["required_diagrams"]),
        docs=tuple(document["required_docs"]),
        forbidden_terms=tuple(language_controls["forbidden"]),
        manifest_json=str(manifest_settings["json_path"]),
        manifest_csv=str(manifest_settings["csv_path"]),
    )


def _load_status_outputs(root: Path) -> dict[str, str]:
    statuses: dict[str, str] = {}
    for path in [
        root / "outputs" / "communication" / "decision_record.json",
        root / "outputs" / "assurance" / "release_readiness.json",
    ]:
        if path.is_file():
            payload = json.loads(path.read_text(encoding="utf-8"))
            for key in ("decision_status", "approval_status", "release_readiness_status"):
                value = payload.get(key)
                if isinstance(value, str):
                    statuses[key] = value
    return statuses


def _validate_required_statuses(root: Path, config: PortfolioConfig) -> list[str]:
    actual = _load_status_outputs(root)
    failures: list[str] = []
    for key, expected in config.required_statuses.items():
        if actual.get(key) != expected:
            failures.append(f"{key} expected {expected!r}, found {actual.get(key)!r}")
    return failures


def _asset_universe(config: PortfolioConfig) -> list[str]:
    return [
        *config.portfolio_assets,
        *config.handover_assets,
        *config.diagrams,
        *config.docs,
        "README.md",
        "config/portfolio.yaml",
    ]


def refresh_portfolio_manifest(
    config_path: Path = Path("config/portfolio.yaml"),
    root: Path = ROOT,
) -> list[str]:
    config = load_portfolio_config(config_path)
    asset_paths = _asset_universe(config)
    excluded = {config.manifest_json, config.manifest_csv}
    missing = validate_assets_exist(
        root,
        [asset for asset in asset_paths if asset not in excluded],
    )
    if missing:
        raise FileNotFoundError(f"Cannot build portfolio manifest; missing assets: {missing}")
    assets = build_manifest(root, asset_paths, excluded=excluded)
    write_manifest(
        root,
        config.manifest_json,
        config.manifest_csv,
        assets,
        _load_status_outputs(root),
    )
    return [asset.path for asset in assets]


def portfolio_check(
    config_path: Path = Path("config/portfolio.yaml"),
    root: Path = ROOT,
    refresh_manifest: bool = True,
) -> ValidationResult:
    config = load_portfolio_config(config_path)
    if refresh_manifest:
        refresh_portfolio_manifest(config_path=config.path, root=root)
    assets = [*config.portfolio_assets, *config.diagrams, *config.docs, "README.md"]
    failures = [
        *validate_assets_exist(root, assets),
        *validate_markdown_text(root, assets, config.forbidden_terms),
        *validate_diagrams(root, list(config.diagrams)),
        *validate_manifest(root, config.manifest_json, config.manifest_csv),
        *_validate_required_statuses(root, config),
    ]
    return ValidationResult(ok=not failures, checked=len(assets), failures=tuple(failures))


def handover_check(
    config_path: Path = Path("config/portfolio.yaml"),
    root: Path = ROOT,
) -> ValidationResult:
    config = load_portfolio_config(config_path)
    failures = [
        *validate_assets_exist(root, list(config.handover_assets)),
        *validate_markdown_text(root, list(config.handover_assets), config.forbidden_terms),
        *_validate_required_statuses(root, config),
    ]
    return ValidationResult(
        ok=not failures,
        checked=len(config.handover_assets),
        failures=tuple(failures),
    )


def final_audit(
    config_path: Path = Path("config/portfolio.yaml"),
    root: Path = ROOT,
) -> ValidationResult:
    config = load_portfolio_config(config_path)
    audit_path = root / "docs" / "final_milestone_audit.md"
    failures = validate_assets_exist(root, list(config.docs))
    if audit_path.is_file():
        audit_text = audit_path.read_text(encoding="utf-8")
        for milestone in range(1, 15):
            if f"Milestone {milestone}" not in audit_text:
                failures.append(f"final audit missing Milestone {milestone}")
        for required in config.required_statuses.values():
            if required not in audit_text:
                failures.append(f"final audit missing status {required}")
    failures.extend(_validate_required_statuses(root, config))
    return ValidationResult(ok=not failures, checked=14, failures=tuple(failures))


def project_summary(root: Path = ROOT) -> dict[str, Any]:
    statuses: dict[str, Any] = _load_status_outputs(root)
    assurance_summary_path = root / "outputs" / "assurance" / "assurance_run_summary.json"
    if assurance_summary_path.is_file():
        statuses.update(json.loads(assurance_summary_path.read_text(encoding="utf-8")))
    decision_record_path = root / "outputs" / "communication" / "decision_record.json"
    if decision_record_path.is_file():
        payload = json.loads(decision_record_path.read_text(encoding="utf-8"))
        lineage = payload.get("evidence_lineage", {})
        if isinstance(lineage, dict):
            statuses["evidence_lineage"] = lineage
        statuses["communication_run_id"] = payload.get("communication_run_id")
    return statuses
