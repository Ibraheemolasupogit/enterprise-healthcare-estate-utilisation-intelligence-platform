from pathlib import Path

import pytest

from estate_intelligence.financial.models import FinanceConfig


def test_finance_config_validates_milestone_contract() -> None:
    config = FinanceConfig.from_yaml(Path("config/finance.yaml"))

    assert config.milestone_owner == "Milestone 10"
    assert config.currency == "GBP"
    assert config.analysis_horizon_years == 5
    assert len(config.financial_case_catalogue) == 7


def test_finance_config_rejects_wrong_owner(tmp_path: Path) -> None:
    payload = (
        Path("config/finance.yaml")
        .read_text()
        .replace('milestone_owner: "Milestone 10"', 'milestone_owner: "Milestone 9"')
    )
    path = tmp_path / "finance.yaml"
    path.write_text(payload)

    with pytest.raises(ValueError, match="Milestone 10"):
        FinanceConfig.from_yaml(path)
