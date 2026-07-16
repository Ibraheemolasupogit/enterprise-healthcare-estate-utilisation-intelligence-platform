from pathlib import Path

import yaml


def test_finance_configuration_contract() -> None:
    config = yaml.safe_load(Path("config/finance.yaml").read_text(encoding="utf-8"))

    assert config["milestone_owner"] == "Milestone 10"
    assert config["currency"] == "GBP"
    assert len(config["financial_case_catalogue"]) == 7
    assert "simulation_risk_adjustments" in config
    assert "guaranteed_savings" not in Path("config/finance.yaml").read_text(encoding="utf-8")


def test_financial_schema_contract() -> None:
    schema = Path("database/schema/012_financial_tables.sql").read_text(encoding="utf-8")

    for table in [
        "evidence_financial_runs",
        "evidence_financial_case_catalogue",
        "evidence_financial_cashflows",
        "evidence_financial_sensitivity",
        "evidence_financial_comparison",
    ]:
        assert table in schema
    assert "idx_financial_readiness" in schema
