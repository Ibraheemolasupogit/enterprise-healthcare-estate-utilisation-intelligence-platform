from pathlib import Path

import pytest

from dashboard.data.repository import DashboardDataError, DashboardRepository, database_uri
from dashboard.data.services import DashboardService

DATABASE = Path("data/processed/estate_intelligence.db")


def test_dashboard_uses_sqlite_read_only_uri_and_blocks_writes() -> None:
    repository = DashboardRepository(DATABASE)

    assert database_uri(DATABASE).startswith("file:")
    assert "mode=ro" in database_uri(DATABASE)
    assert repository.assert_write_blocked()


def test_dashboard_no_arbitrary_sql_execution() -> None:
    repository = DashboardRepository(DATABASE)

    with pytest.raises(DashboardDataError):
        repository.fetch_all("CREATE TABLE should_not_exist (id INTEGER)")


def test_dashboard_services_expose_all_required_views() -> None:
    service = DashboardService(DATABASE)

    assert service.get_estate_portfolio()
    assert service.get_room_utilisation()
    assert service.get_clinical_activity()
    assert service.get_workforce_metrics()["simulation_bottlenecks"]
    assert service.get_data_quality_summary()["manual_review"]
    assert service.get_forecast_summary()["selections"]
    assert service.get_scenario_comparison()["comparison"]
    assert service.get_optimisation_summary()["comparison"]
    assert service.get_simulation_summary()["resilience"]
    assert service.get_financial_summary()["comparison"]
