from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_optimisation_config_contract() -> None:
    document = yaml.safe_load((ROOT / "config" / "optimisation.yaml").read_text())

    assert document["milestone_owner"] == "Milestone 8"
    assert document["solver"] == "scipy_milp_highs"
    assert document["solver_threads"] == 1
    assert len(document["optimisation_cases"]) == 4
    assert "unmet_demand_penalty_per_hour" in document["cost_coefficients"]


def test_optimisation_schema_contract() -> None:
    schema = (ROOT / "database" / "schema" / "010_optimisation_tables.sql").read_text()

    assert "evidence_optimisation_runs" in schema
    assert "evidence_optimisation_candidates" in schema
    assert "evidence_optimisation_solver_results" in schema
    assert "evidence_optimisation_comparison" in schema
