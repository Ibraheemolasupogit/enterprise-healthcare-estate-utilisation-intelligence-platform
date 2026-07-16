from pathlib import Path

from estate_intelligence.assurance.pipeline import run_assurance, verify_assurance


def test_assurance_pipeline_generates_release_evidence(tmp_path: Path) -> None:
    summary = run_assurance(
        Path("data/processed/estate_intelligence.db"),
        Path("config/assurance.yaml"),
        tmp_path,
        "canonical",
        rebuild=True,
    )
    verified = verify_assurance(Path("data/processed/estate_intelligence.db"), tmp_path)

    assert summary["assurance_run_id"].startswith("ASR-")
    assert summary["required_failures"] == 0
    assert verified["output_count"] == 14
