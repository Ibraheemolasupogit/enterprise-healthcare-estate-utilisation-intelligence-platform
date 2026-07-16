from pathlib import Path

from typer.testing import CliRunner

from estate_intelligence.cli import app
from estate_intelligence.ingestion.loader import build_curated_database


def test_run_verify_and_export_data_quality_cli(tmp_path: Path) -> None:
    runner = CliRunner()
    database = tmp_path / "estate.db"
    export_dir = tmp_path / "quality"
    build_curated_database(input_dir=Path("data/sample"), database_path=database, rebuild=True)

    run = runner.invoke(
        app,
        [
            "run-data-quality",
            "--database",
            str(database),
            "--export-dir",
            str(export_dir),
            "--rebuild",
        ],
    )
    verify = runner.invoke(app, ["verify-data-quality", "--database", str(database)])
    export = runner.invoke(
        app,
        [
            "export-data-quality-evidence",
            "--database",
            str(database),
            "--export-dir",
            str(export_dir),
        ],
    )

    assert run.exit_code == 0
    assert "Data-quality run complete" in run.stdout
    assert verify.exit_code == 0
    assert "verification passed" in verify.stdout
    assert export.exit_code == 0
    assert "quality_record_issues.csv" in export.stdout
