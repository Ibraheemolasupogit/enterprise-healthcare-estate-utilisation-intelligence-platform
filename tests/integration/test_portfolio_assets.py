from pathlib import Path

from estate_intelligence.portfolio.service import load_portfolio_config, portfolio_check

ROOT = Path(__file__).resolve().parents[2]


def test_portfolio_assets_exist_and_validate() -> None:
    config = load_portfolio_config()
    missing = [asset for asset in config.portfolio_assets if not (ROOT / asset).is_file()]

    assert missing == []
    assert portfolio_check(refresh_manifest=True).ok is True


def test_portfolio_diagrams_are_mermaid_files() -> None:
    config = load_portfolio_config()

    for diagram in config.diagrams:
        text = (ROOT / diagram).read_text(encoding="utf-8")
        assert text.startswith("flowchart ")
