from pathlib import Path

from estate_intelligence.forecasting.engine import run_forecasting
from estate_intelligence.ingestion.loader import build_curated_database
from estate_intelligence.metrics.engine import calculate_utilisation
from estate_intelligence.scenarios.engine import run_scenarios
from estate_intelligence.validation.engine import run_data_quality


def test_scenario_pipeline_is_deterministic(tmp_path: Path) -> None:
    first = _run(tmp_path / "a.db", tmp_path / "a")
    second = _run(tmp_path / "b.db", tmp_path / "b")
    assert first["scenario_run_id"] == second["scenario_run_id"]
    assert first["scenario_count"] == 4


def _run(database: Path, output: Path) -> dict[str, object]:
    build_curated_database(input_dir=Path("data/sample"), database_path=database, rebuild=True)
    run_data_quality(database_path=database, output_dir=None, rebuild=True)
    calculate_utilisation(database_path=database, output_dir=None, rebuild=True)
    run_forecasting(database_path=database, output_dir=None, rebuild=True)
    return run_scenarios(database_path=database, output_dir=output, rebuild=True)
