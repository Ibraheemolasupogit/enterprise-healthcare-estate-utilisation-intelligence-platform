from pathlib import Path

from estate_intelligence.portfolio.service import handover_check, load_portfolio_config

ROOT = Path(__file__).resolve().parents[2]


def test_handover_assets_exist_and_validate() -> None:
    config = load_portfolio_config()
    missing = [asset for asset in config.handover_assets if not (ROOT / asset).is_file()]

    assert missing == []
    assert handover_check().ok is True
