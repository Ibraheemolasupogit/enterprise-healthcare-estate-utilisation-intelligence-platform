from pathlib import Path

from estate_intelligence.portfolio.service import final_audit

ROOT = Path(__file__).resolve().parents[2]


def test_final_audit_covers_all_milestones() -> None:
    text = (ROOT / "docs" / "final_milestone_audit.md").read_text(encoding="utf-8")

    for milestone in range(1, 15):
        assert f"Milestone {milestone}" in text


def test_final_audit_status_check_passes() -> None:
    assert final_audit().ok is True
