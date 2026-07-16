from pathlib import Path

from typer.testing import CliRunner

from estate_intelligence.cli import app

ROOT = Path(__file__).resolve().parents[2]


def test_final_portfolio_pack_cli_checks_pass() -> None:
    runner = CliRunner()

    for command in ("portfolio-check", "handover-check", "final-audit"):
        result = runner.invoke(app, [command, "--config", str(ROOT / "config" / "portfolio.yaml")])
        assert result.exit_code == 0, result.output


def test_portfolio_manifest_files_are_written() -> None:
    assert (ROOT / "portfolio" / "manifests" / "portfolio_manifest.json").is_file()
    assert (ROOT / "portfolio" / "manifests" / "portfolio_manifest.csv").is_file()
