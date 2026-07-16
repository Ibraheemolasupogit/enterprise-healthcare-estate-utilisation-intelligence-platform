from estate_intelligence.scenarios.capacity import capacity_row


def test_capacity_row_calculates_headroom_and_shortfall() -> None:
    row = capacity_row(
        point_demand=10,
        interval_demand=12,
        planning_demand=12,
        available_hours=20,
        compatible_hours=15,
        retained_rooms=2,
        deactivated_rooms=1,
        protected_rooms=1,
        specialist_rooms=1,
        contingency_rate=0.1,
    )
    assert row["capacity_headroom"] == 3
    assert row["capacity_shortfall"] == 0
    assert row["contingency_headroom"] == 1.8
