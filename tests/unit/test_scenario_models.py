from pathlib import Path

from estate_intelligence.scenarios.models import ScenarioConfig


def test_scenario_config_loads_and_weights_sum_to_one() -> None:
    config = ScenarioConfig.from_yaml(Path("config/scenarios.yaml"))
    assert len(config.scenario_catalogue) == 4
    assert round(sum(config.scoring_weights.values()), 8) == 1.0
