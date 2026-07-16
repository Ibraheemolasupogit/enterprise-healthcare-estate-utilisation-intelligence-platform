from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_simulation_config_contract() -> None:
    document = yaml.safe_load((ROOT / "config" / "simulation.yaml").read_text())

    assert document["milestone_owner"] == "Milestone 9"
    assert document["time_unit"] == "minutes"
    assert document["replications"] == 30
    assert len(document["experiment_catalogue"]) == 6
    assert "maximum_p95_wait_minutes" in document["performance_thresholds"]


def test_simulation_schema_contract() -> None:
    schema = (ROOT / "database" / "schema" / "011_simulation_tables.sql").read_text()

    assert "evidence_simulation_runs" in schema
    assert "evidence_simulation_replications" in schema
    assert "evidence_simulation_resilience_metrics" in schema
    assert "evidence_simulation_threshold_results" in schema
