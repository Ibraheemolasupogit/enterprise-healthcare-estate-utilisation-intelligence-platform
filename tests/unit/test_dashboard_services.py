from pathlib import Path

import pytest
from typer.testing import CliRunner

from dashboard.data.repository import DashboardDataError, DashboardRepository
from dashboard.data.services import DashboardService
from estate_intelligence.cli import app


def test_dashboard_lineage_and_executive_summary_resolve_from_database(
    dashboard_database: Path,
) -> None:
    service = DashboardService(dashboard_database)
    lineage = service.get_run_lineage()

    assert lineage["financial"] == "FIN-fixture"
    assert lineage["simulation"] == "SIM-fixture"

    summary = service.get_executive_summary()
    assert summary["site_count"] == 1
    assert summary["room_count"] == 1
    assert summary["simulation_readiness"] == "review_required"
    assert summary["financial_readiness"] == "review_required"
    assert "Simulation readiness is review_required." in summary["warnings"]
    assert "Financial confidence is not_realisable_without_mitigation." in summary["warnings"]


def test_dashboard_missing_database_is_reported() -> None:
    service = DashboardService(Path("data/processed/missing-dashboard.db"))

    with pytest.raises(FileNotFoundError):
        service.validate()


def test_dashboard_cli_check_fails_for_missing_explicit_database(tmp_path: Path) -> None:
    missing = tmp_path / "missing-dashboard.db"

    result = CliRunner().invoke(app, ["dashboard-check", "--database", str(missing)])

    assert result.exit_code == 2
    assert "Dashboard check failed: Dashboard database not found" in result.output


def test_dashboard_repository_rejects_mutating_sql(dashboard_database: Path) -> None:
    repository = DashboardRepository(dashboard_database)

    with pytest.raises(DashboardDataError):
        repository.fetch_all("DELETE FROM curated_rooms")
