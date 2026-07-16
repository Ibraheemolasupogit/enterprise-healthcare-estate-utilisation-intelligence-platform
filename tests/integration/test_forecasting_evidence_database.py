from pathlib import Path

from estate_intelligence.forecasting.engine import run_forecasting, verify_forecasting
from estate_intelligence.ingestion.loader import build_curated_database
from estate_intelligence.metrics.engine import calculate_utilisation
from estate_intelligence.validation.engine import run_data_quality


def test_forecasting_evidence_database_counts(tmp_path: Path) -> None:
    database = tmp_path / "forecast.db"
    build_curated_database(
        input_dir=Path("data/sample"),
        database_path=database,
        export_dir=None,
        rebuild=True,
    )
    run_data_quality(database_path=database, output_dir=None, rebuild=True)
    calculate_utilisation(database_path=database, output_dir=None, rebuild=True)
    run_forecasting(database_path=database, output_dir=None, rebuild=True)
    summary = verify_forecasting(database)
    assert summary["series_count"] == 78
    assert summary["forecast_value_count"] == 78 * 6
