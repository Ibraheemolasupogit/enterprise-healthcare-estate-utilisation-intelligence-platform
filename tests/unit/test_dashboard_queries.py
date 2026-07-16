from dashboard.data.queries import REQUIRED_EVIDENCE_TABLES, RUN_TABLES


def test_dashboard_queries_define_required_lineage_and_tables() -> None:
    assert set(RUN_TABLES) == {
        "ingestion",
        "quality",
        "utilisation",
        "forecast",
        "scenario",
        "optimisation",
        "simulation",
        "financial",
    }
    assert "evidence_financial_comparison" in REQUIRED_EVIDENCE_TABLES
    assert "curated_rooms" in REQUIRED_EVIDENCE_TABLES
