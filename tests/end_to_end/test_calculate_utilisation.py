from pathlib import Path

from typer.testing import CliRunner

from estate_intelligence.cli import app
from estate_intelligence.ingestion.loader import build_curated_database
from estate_intelligence.validation.engine import run_data_quality


def test_calculate_verify_export_utilisation_cli(tmp_path: Path) -> None:
    runner = CliRunner()
    database = tmp_path / "estate.db"
    export_dir = tmp_path / "utilisation"
    build_curated_database(input_dir=Path("data/sample"), database_path=database, rebuild=True)
    run_data_quality(database_path=database, rebuild=True)

    calculate = runner.invoke(
        app,
        [
            "calculate-utilisation",
            "--database",
            str(database),
            "--output-dir",
            str(export_dir),
            "--rebuild",
        ],
    )
    verify = runner.invoke(app, ["verify-utilisation", "--database", str(database)])
    export = runner.invoke(
        app,
        [
            "export-utilisation-evidence",
            "--database",
            str(database),
            "--output-dir",
            str(export_dir),
        ],
    )

    assert calculate.exit_code == 0
    assert "Utilisation calculation complete" in calculate.stdout
    assert verify.exit_code == 0
    assert "Utilisation verification passed" in verify.stdout
    assert export.exit_code == 0
    assert "room_utilisation.csv" in export.stdout
