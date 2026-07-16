from pathlib import Path

from estate_intelligence.ingestion.loader import build_curated_database
from estate_intelligence.validation.engine import run_data_quality, verify_data_quality


def test_data_quality_pipeline_detects_milestone_2_defects(tmp_path: Path) -> None:
    database = tmp_path / "estate.db"
    export_dir = tmp_path / "quality"
    build_curated_database(input_dir=Path("data/sample"), database_path=database, rebuild=True)

    summary = run_data_quality(database_path=database, output_dir=export_dir, rebuild=True)
    verified = verify_data_quality(database)

    assert summary["overall_status"] == "pass_with_warnings"
    assert summary["issue_count"] == 6
    assert summary["manual_review_count"] == 4
    assert verified["critical_unexpected_issues"] == 0
    assert (export_dir / "quality_run_summary.json").is_file()
    assert (export_dir / "intentional_defect_detection.csv").is_file()
