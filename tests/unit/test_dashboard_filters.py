from pathlib import Path

from dashboard.data.services import DashboardService

DATABASE = Path("data/processed/estate_intelligence.db")


def test_dashboard_building_and_room_filters_are_parameterised() -> None:
    service = DashboardService(DATABASE)

    buildings = service.get_estate_portfolio({"site_id": "SITE-01"})
    rooms = service.get_room_utilisation({"protected_capacity_flag": 1})

    assert buildings
    assert all(row["site_id"] == "SITE-01" for row in buildings)
    assert rooms
    assert all(row["protected_capacity_flag"] == 1 for row in rooms)
