from estate_intelligence.validation.consistency import consistency_rules


def test_consistency_rules_include_known_cross_field_controls() -> None:
    rules = set(consistency_rules())

    assert {"DQ-BKG-CON-001", "DQ-FIN-CON-001", "DQ-WRK-CON-001"}.issubset(rules)
