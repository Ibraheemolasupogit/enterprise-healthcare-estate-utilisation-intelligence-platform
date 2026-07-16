from estate_intelligence.optimisation.candidates import _source_site


def test_source_site_is_deterministic_by_available_fte_then_site() -> None:
    workforce = {
        ("SVC-001", "SITE-02"): {"available": 4.0, "planned": 5.0},
        ("SVC-001", "SITE-01"): {"available": 4.0, "planned": 5.0},
    }

    assert _source_site("SVC-001", workforce) == "SITE-01"
