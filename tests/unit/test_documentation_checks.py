from pathlib import Path

from estate_intelligence.assurance.validation import validate_docs

ROOT = Path(__file__).resolve().parents[2]


def test_required_assurance_docs_exist_without_placeholders() -> None:
    required = [
        "assurance_framework.md",
        "ci_cd_strategy.md",
        "release_gates.md",
        "reproducibility_assurance.md",
        "security_assurance.md",
        "release_evidence.md",
        "developer_quality_workflow.md",
    ]

    assert validate_docs(ROOT, required) == []
