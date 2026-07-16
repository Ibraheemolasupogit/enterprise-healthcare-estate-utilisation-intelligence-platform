from datetime import date

from estate_intelligence.metrics.availability import applicable_weeks, available_room_hours


def test_available_room_hours_for_active_room() -> None:
    weeks = applicable_weeks(date(2024, 4, 1), date(2024, 4, 14))

    assert weeks == 2
    assert available_room_hours(50, weeks) == 100


def test_inactive_room_has_zero_available_hours() -> None:
    assert available_room_hours(50, 2, active=False) == 0
