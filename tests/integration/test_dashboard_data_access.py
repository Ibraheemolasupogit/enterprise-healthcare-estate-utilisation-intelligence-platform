from pathlib import Path

import pytest

from dashboard.data.repository import DashboardDataError, DashboardRepository, database_uri
from dashboard.data.services import DashboardService


def test_dashboard_uses_sqlite_read_only_uri_and_blocks_writes(dashboard_database: Path) -> None:
    repository = DashboardRepository(dashboard_database)

    assert database_uri(dashboard_database).startswith("file:")
    assert "mode=ro" in database_uri(dashboard_database)
    assert repository.assert_write_blocked()


def test_dashboard_no_arbitrary_sql_execution(dashboard_database: Path) -> None:
    repository = DashboardRepository(dashboard_database)

    with pytest.raises(DashboardDataError):
        repository.fetch_all("CREATE TABLE should_not_exist (id INTEGER)")


def test_dashboard_services_resolve_lineage_warnings_and_core_views(
    dashboard_database: Path,
) -> None:
    service = DashboardService(dashboard_database)
    summary = service.validate()

    assert summary.ok
    assert summary.run_lineage["ingestion"] == "ING-fixture"
    assert "Simulation readiness is review_required." in summary.warnings
    assert "Financial confidence is not_realisable_without_mitigation." in summary.warnings
    assert service.get_estate_portfolio()
    assert service.get_room_utilisation()
    assert service.get_workforce_metrics()["simulation_bottlenecks"]
