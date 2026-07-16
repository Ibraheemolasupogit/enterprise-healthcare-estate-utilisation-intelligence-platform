from estate_intelligence.validation.validity import validity_rules


def test_validity_rules_cover_all_datasets() -> None:
    assert len(validity_rules()) == 8
