from pathlib import Path

from typer.testing import CliRunner

from estate_intelligence.cli import app


def test_generate_and_verify_cli_round_trip(tmp_path: Path) -> None:
    runner = CliRunner()
    output_dir = tmp_path / "synthetic"

    generate = runner.invoke(app, ["generate-data", "--sample", "--output-dir", str(output_dir)])
    verify = runner.invoke(app, ["verify-synthetic-data", "--output-dir", str(output_dir)])

    assert generate.exit_code == 0
    assert "bookings: 1440" in generate.stdout
    assert verify.exit_code == 0
    assert "verification passed" in verify.stdout


def test_generate_cli_refuses_overwrite(tmp_path: Path) -> None:
    runner = CliRunner()
    output_dir = tmp_path / "synthetic"

    first = runner.invoke(app, ["generate-data", "--sample", "--output-dir", str(output_dir)])
    second = runner.invoke(app, ["generate-data", "--sample", "--output-dir", str(output_dir)])

    assert first.exit_code == 0
    assert second.exit_code == 2
    assert "Refusing to overwrite" in second.stderr


def test_verify_cli_fails_for_missing_metadata(tmp_path: Path) -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["verify-synthetic-data", "--output-dir", str(tmp_path)])

    assert result.exit_code == 2
    assert "Missing generation metadata" in result.stderr
