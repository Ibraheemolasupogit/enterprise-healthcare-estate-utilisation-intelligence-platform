from pathlib import Path

from estate_intelligence.reporting.service import (
    generate_communication_evidence,
    verify_communication_evidence,
)


def test_communication_pipeline_generates_required_outputs(tmp_path: Path) -> None:
    output_dir = tmp_path / "communication"

    summary = generate_communication_evidence(
        Path("data/processed/estate_intelligence.db"),
        output_dir=output_dir,
        rebuild=True,
    )
    verified = verify_communication_evidence(
        Path("data/processed/estate_intelligence.db"),
        output_dir=output_dir,
    )

    assert summary["communication_run_id"] == verified["communication_run_id"]
    assert (output_dir / "executive_options_paper.md").exists()
    assert (output_dir / "decision_record.json").exists()
