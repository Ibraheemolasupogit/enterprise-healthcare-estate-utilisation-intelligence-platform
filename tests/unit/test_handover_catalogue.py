from estate_intelligence.portfolio.service import handover_check, load_portfolio_config


def test_handover_catalogue_contains_expected_assets() -> None:
    config = load_portfolio_config()

    assert len(config.handover_assets) == 15
    assert "handover/governance_boundaries.md" in config.handover_assets
    assert "handover/known_issues.md" in config.handover_assets


def test_handover_check_passes() -> None:
    assert handover_check().ok is True
