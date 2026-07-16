from pathlib import Path

import pytest

from dashboard.data.repository import DashboardDataError, DashboardRepository
from dashboard.data.services import DashboardService

DATABASE = Path("data/processed/estate_intelligence.db")


def test_dashboard_lineage_and_executive_summary_resolve_from_database() -> None:
    service = DashboardService(DATABASE)
    lineage = service.get_run_lineage()

    assert lineage["financial"].startswith("FIN-")
    assert lineage["simulation"].startswith("SIM-")

    summary = service.get_executive_summary()
    assert summary["site_count"] == 4
    assert summary["room_count"] == 54
    assert summary["simulation_readiness"] == "review_required"
    assert summary["financial_readiness"] == "review_required"


def test_dashboard_missing_database_is_reported() -> None:
    service = DashboardService(Path("data/processed/missing-dashboard.db"))

    with pytest.raises(FileNotFoundError):
        service.validate()


def test_dashboard_repository_rejects_mutating_sql() -> None:
    repository = DashboardRepository(DATABASE)

    with pytest.raises(DashboardDataError):
        repository.fetch_all("DELETE FROM curated_rooms")
