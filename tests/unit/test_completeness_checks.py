from estate_intelligence.validation.completeness import completeness_rules


def test_completeness_rules_include_room_optional_source_control() -> None:
    assert "DQ-ROM-CMP-001" in completeness_rules()
