from estate_intelligence.validation.reconciliation import reconciliation_rules


def test_reconciliation_rules_cover_all_eight_datasets() -> None:
    assert len(reconciliation_rules()) == 8
