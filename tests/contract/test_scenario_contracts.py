from pathlib import Path

from estate_intelligence.scenarios.models import ScenarioConfig


def test_scenario_contract_contains_required_scenarios() -> None:
    config = ScenarioConfig.from_yaml(Path("config/scenarios.yaml"))
    assert {item.scenario_id for item in config.scenario_catalogue} == {
        "baseline",
        "light_consolidation",
        "site_consolidation",
        "hybrid_redesign",
    }
    assert config.forecast_interval_basis == "upper_80"
