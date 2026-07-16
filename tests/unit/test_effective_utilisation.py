from estate_intelligence.metrics.utilisation import effective_utilisation_score


def test_effective_utilisation_uses_configured_weights() -> None:
    weights = {"actual_occupied_utilisation": 0.6, "attendance_utilisation": 0.4}
    components = {"actual_occupied_utilisation": 0.5, "attendance_utilisation": 1.0}

    assert effective_utilisation_score(components, weights) == 0.7


def test_effective_utilisation_missing_components_are_zero() -> None:
    assert effective_utilisation_score({}, {"actual_occupied_utilisation": 1.0}) == 0
