import sqlite3

from estate_intelligence.forecasting.aggregation import month_keys, room_hours


def test_month_calendar_and_room_hour_derivation() -> None:
    assert month_keys("2024-04-01", "2024-06-30") == ["2024-04", "2024-05", "2024-06"]
    assert room_hours(10, 30) == 5


def test_sqlite_import_available_for_pipeline_fixtures() -> None:
    assert sqlite3.sqlite_version
