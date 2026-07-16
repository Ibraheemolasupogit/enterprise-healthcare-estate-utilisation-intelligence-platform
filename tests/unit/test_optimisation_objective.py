from estate_intelligence.optimisation.objective import OBJECTIVE_UNITS


def test_objective_components_are_documented() -> None:
    assert "unmet_demand_penalty" in OBJECTIVE_UNITS
    assert OBJECTIVE_UNITS["retained_recurring_estate_cost"] == "synthetic_currency"
    assert OBJECTIVE_UNITS["travel_penalty"] == "synthetic_penalty"
