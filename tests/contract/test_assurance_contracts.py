from pathlib import Path

import yaml

from estate_intelligence.assurance.pipeline import ASSURANCE_OUTPUTS

ROOT = Path(__file__).resolve().parents[2]


def test_assurance_config_contract() -> None:
    document = yaml.safe_load((ROOT / "config" / "assurance.yaml").read_text(encoding="utf-8"))

    assert document["framework_version"] == "m13-v1"
    assert document["coverage_threshold"] >= 85
    assert document["communication_checks"]["required_approval_status"] == "not_approved"


def test_assurance_output_contract() -> None:
    assert ASSURANCE_OUTPUTS == [
        "assurance_run_summary.json",
        "assurance_check_catalogue.csv",
        "assurance_check_results.csv",
        "assurance_failures.csv",
        "assurance_warnings.csv",
        "assurance_reproducibility.csv",
        "assurance_security_findings.csv",
        "assurance_documentation_results.csv",
        "assurance_release_gates.csv",
        "release_manifest.json",
        "release_manifest.csv",
        "release_readiness.json",
        "release_readiness.md",
        "assurance_report.md",
    ]
