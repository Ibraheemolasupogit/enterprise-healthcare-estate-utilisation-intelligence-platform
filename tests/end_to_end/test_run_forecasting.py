from pathlib import Path

from typer.testing import CliRunner

from estate_intelligence.cli import app
from estate_intelligence.ingestion.loader import build_curated_database
from estate_intelligence.metrics.engine import calculate_utilisation
from estate_intelligence.validation.engine import run_data_quality


def test_run_forecasting_cli(tmp_path: Path) -> None:
    database = tmp_path / "cli.db"
    build_curated_database(
        input_dir=Path("data/sample"),
        database_path=database,
        export_dir=None,
        rebuild=True,
    )
    run_data_quality(database_path=database, output_dir=None, rebuild=True)
    calculate_utilisation(database_path=database, output_dir=None, rebuild=True)
    result = CliRunner().invoke(
        app,
        [
            "run-forecasting",
            "--database",
            str(database),
            "--output-dir",
            str(tmp_path / "forecasting"),
            "--rebuild",
        ],
    )
    assert result.exit_code == 0
    assert "Forecasting run complete" in result.output
