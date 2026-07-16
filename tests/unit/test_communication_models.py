from pathlib import Path

from estate_intelligence.reporting.service import load_communication_config


def test_communication_config_has_required_profiles_and_rules() -> None:
    config = load_communication_config(Path("config/communication.yaml"))

    assert config.framework_version == "m12-v1"
    assert len(config.document["audience_catalogue"]) == 5
    assert config.document["decision_record_schema"]["approval_status"] == "not_approved"
