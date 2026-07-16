from estate_intelligence.metrics.finance import annual_operating_cost, unit_cost


def test_unit_cost_uses_configured_recurring_components_only() -> None:
    row: dict[str, object] = {
        "lease_cost": "10",
        "maintenance_cost": "5",
        "planned_capital_cost": "1000",
    }

    assert annual_operating_cost(row, ("lease_cost", "maintenance_cost")) == 15
    assert unit_cost(15, 3) == 5
    assert unit_cost(15, 0) == 0
