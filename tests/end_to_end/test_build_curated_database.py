from pathlib import Path

from typer.testing import CliRunner

from estate_intelligence.cli import app


def test_build_verify_export_cli_round_trip(tmp_path: Path) -> None:
    runner = CliRunner()
    database = tmp_path / "estate.db"
    export_dir = tmp_path / "evidence"

    build = runner.invoke(
        app,
        [
            "build-curated-database",
            "--input-dir",
            "data/sample",
            "--database",
            str(database),
            "--export-dir",
            str(export_dir),
            "--rebuild",
        ],
    )
    verify = runner.invoke(app, ["verify-database", "--database", str(database)])
    export = runner.invoke(
        app,
        ["export-ingestion-evidence", "--database", str(database), "--export-dir", str(export_dir)],
    )

    assert build.exit_code == 0
    assert "ING-3e1bb14611c3612e" in build.stdout
    assert verify.exit_code == 0
    assert "5 intentional issues detected" in verify.stdout
    assert export.exit_code == 0
