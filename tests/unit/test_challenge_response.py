from pathlib import Path

from estate_intelligence.reporting.challenge import build_challenge_responses, build_objections
from estate_intelligence.reporting.service import load_communication_config


def test_challenge_responses_include_supported_objections() -> None:
    config = load_communication_config(Path("config/communication.yaml"))
    objections = build_objections(list(config.document["challenge_catalogue"]))
    responses = build_challenge_responses(objections)

    assert len(objections) == 10
    assert len(responses) == 10
    assert any(objection.status == "supported" for objection in objections)
    assert all(
        objection.scenario_label == "synthetic challenge scenario" for objection in objections
    )
