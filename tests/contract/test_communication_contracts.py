from pathlib import Path

from estate_intelligence.reporting.service import load_communication_config


def test_communication_config_has_required_non_approval_statuses() -> None:
    config = load_communication_config(Path("config/communication.yaml"))

    schema = config.document["decision_record_schema"]

    assert schema["decision_status"] == "awaiting_governance_decision"
    assert schema["approval_status"] == "not_approved"


def test_communication_config_contains_required_audiences_and_language_controls() -> None:
    config = load_communication_config(Path("config/communication.yaml"))

    assert {audience["audience_id"] for audience in config.document["audience_catalogue"]} == {
        "executive",
        "clinical_operational",
        "finance",
        "estates",
        "technical",
    }
    assert config.document["status_language_rules"]["implementation_status"] == "not_approved"
    assert (
        config.document["risk_language_rules"]["resilience_failed_suffix"]
        == "not realisable without mitigation"
    )
