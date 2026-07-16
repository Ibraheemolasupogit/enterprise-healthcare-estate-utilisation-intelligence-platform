import csv
import json
from pathlib import Path

from estate_intelligence.synthetic_data.common import sha256_file
from estate_intelligence.synthetic_data.generator import DATASET_COLUMNS

ROOT = Path(__file__).resolve().parents[2]
SAMPLE = ROOT / "data" / "sample"


def test_committed_sample_files_exist_and_are_small() -> None:
    for dataset_name in DATASET_COLUMNS:
        path = SAMPLE / f"{dataset_name}.csv"
        assert path.is_file()
        assert path.stat().st_size < 600_000


def test_committed_sample_csv_headers_match_contract() -> None:
    for dataset_name, columns in DATASET_COLUMNS.items():
        with (SAMPLE / f"{dataset_name}.csv").open(encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle)
            assert next(reader) == columns


def test_committed_metadata_and_quality_issues_parse() -> None:
    metadata = json.loads((SAMPLE / "generation_metadata.json").read_text(encoding="utf-8"))
    issues = json.loads((SAMPLE / "data_quality_issues.json").read_text(encoding="utf-8"))

    assert metadata["master_seed"] == 20260714
    assert metadata["intentional_quality_issue_count"] == 5
    assert len(issues["issues"]) == 5
    assert all(issue["intentional"] is True for issue in issues["issues"])
    duplicate_issue = next(issue for issue in issues["issues"] if issue["issue_id"] == "DQ-0001")
    assert duplicate_issue["duplicate_business_key"] == "BLD-002|treatment 8"
    assert duplicate_issue["duplicate_group_members"] == ["ROOM-0002", "ROOM-0026"]


def test_committed_metadata_checksums_are_correct() -> None:
    metadata = json.loads((SAMPLE / "generation_metadata.json").read_text(encoding="utf-8"))

    for filename, checksum in metadata["file_checksums"].items():
        assert sha256_file(SAMPLE / filename) == checksum
