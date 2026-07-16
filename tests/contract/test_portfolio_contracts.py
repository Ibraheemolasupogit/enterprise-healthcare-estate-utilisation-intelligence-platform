from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_portfolio_config_contract() -> None:
    document = yaml.safe_load((ROOT / "config" / "portfolio.yaml").read_text(encoding="utf-8"))

    assert document["milestone_owner"] == "Milestone 14"
    assert document["required_statuses"]["decision_status"] == "awaiting_governance_decision"
    assert document["required_statuses"]["approval_status"] == "not_approved"
    assert document["manifest_settings"]["checksum_algorithm"] == "sha256"


def test_portfolio_manifest_contract_after_generation() -> None:
    from estate_intelligence.portfolio.service import portfolio_check

    result = portfolio_check(refresh_manifest=True)
    manifest = yaml.safe_load(
        (ROOT / "portfolio" / "manifests" / "portfolio_manifest.json").read_text(encoding="utf-8")
    )

    assert result.ok is True
    assert manifest["framework_version"] == "m14-v1"
    assert manifest["statuses"]["approval_status"] == "not_approved"
