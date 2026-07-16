from estate_intelligence.validation.timeliness import timeliness_rules


def test_timeliness_rules_are_accept_with_warning_controls() -> None:
    assert len(timeliness_rules()) == 8
    assert all(rule_id.endswith("-TIM-001") for rule_id in timeliness_rules())
