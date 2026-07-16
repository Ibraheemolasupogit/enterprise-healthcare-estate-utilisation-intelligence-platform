from estate_intelligence.scenarios.uncertainty import confidence_status


def test_confidence_status_is_conservative() -> None:
    assert confidence_status(2, 1.0) == "low"
    assert confidence_status(0, -0.1) == "insufficient_evidence"
    assert confidence_status(0, 0.05) == "moderate"
    assert confidence_status(0, 0.5) == "high"
