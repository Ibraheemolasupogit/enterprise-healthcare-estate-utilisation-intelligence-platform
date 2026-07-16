import pytest
from pydantic import ValidationError

from estate_intelligence.validation.models import QualityIssue, QualityRule


def test_quality_rule_is_typed_and_frozen() -> None:
    rule = QualityRule(
        rule_id="DQ-ROM-UNI-001",
        rule_name="Duplicate room names",
        dataset="rooms",
        dimension="uniqueness",
        description="Detect duplicate room labels.",
        severity="warning",
        field_names=("room_name",),
        scope="record",
        threshold="configured",
        expected_outcome="no duplicates",
        failure_action="manual_review",
        downstream_impact="Manual review before analytics.",
    )

    assert rule.milestone_owner == "Milestone 4"
    with pytest.raises(ValidationError):
        rule.enabled = False


def test_quality_rule_rejects_invalid_identifier() -> None:
    with pytest.raises(ValidationError):
        QualityRule(
            rule_id="DQ-bad",
            rule_name="Bad",
            dataset="rooms",
            dimension="uniqueness",
            description="Bad rule.",
            severity="warning",
            field_names=("room_name",),
            scope="record",
            threshold="configured",
            expected_outcome="none",
            failure_action="manual_review",
            downstream_impact="none",
        )


def test_quality_issue_carries_intentional_defect_link() -> None:
    issue = QualityIssue(
        evidence_key="abc",
        rule_id="DQ-BKG-CON-001",
        dataset="bookings",
        record_identifier="BOOK-000025",
        field_name="actual_attendance_count",
        observed_value="13",
        expected_condition="actual <= planned",
        severity="high",
        failure_action="manual_review",
        status="detected",
        issue_description="Attendance exceeds planned.",
        intentional_issue_id="DQ-0003",
    )

    assert issue.intentional_issue_id == "DQ-0003"
