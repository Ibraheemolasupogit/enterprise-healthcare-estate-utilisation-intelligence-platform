from pathlib import Path

from typer.testing import CliRunner

from estate_intelligence.cli import app


def test_generate_verify_export_communication_cli(tmp_path: Path) -> None:
    output_dir = tmp_path / "communication"
    runner = CliRunner()

    generated = runner.invoke(
        app,
        [
            "generate-communication-evidence",
            "--database",
            "data/processed/estate_intelligence.db",
            "--output-dir",
            str(output_dir),
            "--rebuild",
        ],
    )
    assert generated.exit_code == 0
    assert "approval_status: not_approved" in generated.output

    verified = runner.invoke(
        app,
        [
            "verify-communication-evidence",
            "--database",
            "data/processed/estate_intelligence.db",
            "--output-dir",
            str(output_dir),
        ],
    )
    assert verified.exit_code == 0

    exported = runner.invoke(
        app,
        [
            "export-communication-evidence",
            "--database",
            "data/processed/estate_intelligence.db",
            "--output-dir",
            str(output_dir),
        ],
    )
    assert exported.exit_code == 0
    assert "executive_options_paper.md" in exported.output
