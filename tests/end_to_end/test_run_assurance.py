from pathlib import Path

from typer.testing import CliRunner

from estate_intelligence.cli import app


def test_run_assurance_cli(tmp_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "run-assurance",
            "--database",
            "data/processed/estate_intelligence.db",
            "--config",
            "config/assurance.yaml",
            "--output-dir",
            str(tmp_path),
            "--rebuild",
        ],
    )

    assert result.exit_code == 0
    assert "Assurance run complete: ASR-" in result.stdout
