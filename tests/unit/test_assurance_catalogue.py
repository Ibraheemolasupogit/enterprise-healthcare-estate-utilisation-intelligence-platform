from estate_intelligence.assurance.catalogue import build_check_catalogue


def test_assurance_catalogue_has_required_stable_ids() -> None:
    checks = build_check_catalogue()
    ids = [check.check_id for check in checks]

    assert len(checks) == 18
    assert len(ids) == len(set(ids))
    assert ids[0] == "ASR-REP-001"
    assert "ASR-COM-001" in ids
    assert all(check.required for check in checks)
