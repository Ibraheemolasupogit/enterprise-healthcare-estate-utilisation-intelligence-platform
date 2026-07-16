import sqlite3
from pathlib import Path

import yaml

from estate_intelligence.forecasting.engine import run_forecasting
from estate_intelligence.ingestion.loader import build_curated_database
from estate_intelligence.metrics.engine import calculate_utilisation
from estate_intelligence.optimisation.engine import run_optimisation, verify_optimisation
from estate_intelligence.scenarios.engine import run_scenarios
from estate_intelligence.validation.engine import run_data_quality


def test_optimisation_evidence_database_counts(tmp_path: Path) -> None:
    database = tmp_path / "optimisation.db"
    build_curated_database(input_dir=Path("data/sample"), database_path=database, rebuild=True)
    run_data_quality(database_path=database, output_dir=None, rebuild=True)
    calculate_utilisation(database_path=database, output_dir=None, rebuild=True)
    run_forecasting(database_path=database, output_dir=None, rebuild=True)
    run_scenarios(database_path=database, output_dir=None, rebuild=True)
    run_optimisation(database_path=database, output_dir=None, rebuild=True)

    summary = verify_optimisation(database)
    assert summary["case_count"] == 4
    assert summary["candidate_count"] > 0
    assert summary["unmet_demand_hours"] == 0


def test_optimisation_records_controlled_infeasibility(tmp_path: Path) -> None:
    database = tmp_path / "optimisation-infeasible.db"
    build_curated_database(input_dir=Path("data/sample"), database_path=database, rebuild=True)
    run_data_quality(database_path=database, output_dir=None, rebuild=True)
    calculate_utilisation(database_path=database, output_dir=None, rebuild=True)
    run_forecasting(database_path=database, output_dir=None, rebuild=True)
    run_scenarios(database_path=database, output_dir=None, rebuild=True)

    config = yaml.safe_load(Path("config/optimisation.yaml").read_text())
    config["capacity_buffer"] = 0.99
    config["contingency_capacity"] = 0.99
    config["service_continuity_rules"]["prohibit_unmet_mandatory_demand"] = True
    config_path = tmp_path / "optimisation-infeasible.yaml"
    config_path.write_text(yaml.safe_dump(config, sort_keys=False))

    result = run_optimisation(
        database_path=database,
        config_path=config_path,
        output_dir=None,
        rebuild=True,
    )

    assert result["readiness_status"] == "review_required"
    with sqlite3.connect(database) as connection:
        infeasible_cases = connection.execute(
            "SELECT COUNT(*) FROM evidence_optimisation_solver_results "
            "WHERE mapped_status = 'infeasible'"
        ).fetchone()[0]
        diagnostics = connection.execute(
            "SELECT COUNT(*) FROM evidence_optimisation_infeasibility "
            "WHERE diagnostic_type = 'service_period_capacity_shortfall'"
        ).fetchone()[0]

    assert infeasible_cases == 4
    assert diagnostics > 0
