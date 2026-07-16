from pathlib import Path

from estate_intelligence.portfolio.service import load_portfolio_config
from estate_intelligence.portfolio.validation import validate_markdown_text

ROOT = Path(__file__).resolve().parents[2]


def test_portfolio_markdown_respects_language_controls() -> None:
    config = load_portfolio_config()
    assets = [*config.portfolio_assets, *config.docs, "README.md"]

    assert validate_markdown_text(ROOT, list(assets), config.forbidden_terms) == []


def test_handover_markdown_respects_language_controls() -> None:
    config = load_portfolio_config()

    assert validate_markdown_text(ROOT, list(config.handover_assets), config.forbidden_terms) == []
