from estate_intelligence.reporting.decision_record import build_decision_record
from estate_intelligence.reporting.models import (
    ChallengeResponse,
    CommunicationOption,
    CommunicationRun,
    Revision,
)


def test_decision_record_statuses_are_non_approving() -> None:
    run = CommunicationRun(
        communication_run_id="COM-test",
        lineage={"ingestion": "ING", "quality": "DQR"},
        config_checksum="a",
        audience_catalogue_checksum="b",
        option_catalogue_checksum="c",
        challenge_catalogue_checksum="d",
        decision_status="awaiting_governance_decision",
        approval_status="not_approved",
    )
    option = CommunicationOption(
        "OPT-A",
        "Current estate baseline",
        "case_a",
        "financial",
        "descriptive_baseline",
        "fail",
        "not_realisable_without_mitigation",
        0.0,
        0.0,
        "not_reached",
        "risk",
        "financial risk",
        1,
        "not_approved",
    )
    challenge = ChallengeResponse(
        "CHG-001", "OBJ-001", "supported", "evidence", "response", "change", "concern"
    )
    revision = Revision(
        "REV-001", "initial", "CHG-001", "evidence", "revised", "reason", "outputs", "complete"
    )

    record = build_decision_record(run, [option], [challenge], [revision])

    assert record["decision_status"] == "awaiting_governance_decision"
    assert record["approval_status"] == "not_approved"
    assert "OPT-A" in record["options_considered"]
