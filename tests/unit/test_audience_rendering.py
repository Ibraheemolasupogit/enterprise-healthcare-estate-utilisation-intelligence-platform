from pathlib import Path

from estate_intelligence.reporting.audience import load_audiences
from estate_intelligence.reporting.service import load_communication_config


def test_audience_catalogue_has_expected_profiles() -> None:
    config = load_communication_config(Path("config/communication.yaml"))
    audiences = load_audiences(config.document)

    assert {audience.audience_id for audience in audiences} == {
        "executive",
        "clinical_operational",
        "finance",
        "estates",
        "technical",
    }
