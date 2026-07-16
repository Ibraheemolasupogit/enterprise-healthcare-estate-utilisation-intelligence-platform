from estate_intelligence.scenarios.baseline import SCENARIO_TYPE


def test_baseline_marker() -> None:
    assert SCENARIO_TYPE == "baseline"
