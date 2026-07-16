from pathlib import Path

from estate_intelligence.forecasting.engine import run_forecasting
from estate_intelligence.ingestion.loader import build_curated_database
from estate_intelligence.metrics.engine import calculate_utilisation
from estate_intelligence.validation.engine import run_data_quality


def test_forecasting_pipeline_is_deterministic(tmp_path: Path) -> None:
    db_a = tmp_path / "a.db"
    db_b = tmp_path / "b.db"
    for database in (db_a, db_b):
        build_curated_database(
            input_dir=Path("data/sample"),
            database_path=database,
            export_dir=None,
            rebuild=True,
        )
        run_data_quality(database_path=database, output_dir=None, rebuild=True)
        calculate_utilisation(database_path=database, output_dir=None, rebuild=True)
    first = run_forecasting(database_path=db_a, output_dir=tmp_path / "a", rebuild=True)
    second = run_forecasting(database_path=db_b, output_dir=tmp_path / "b", rebuild=True)
    assert first["forecast_run_id"] == second["forecast_run_id"]
    assert first["series_count"] == second["series_count"]
