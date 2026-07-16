from estate_intelligence.optimisation.diagnostics import is_material_unmet_demand
from estate_intelligence.optimisation.results import case_is_feasible


def test_unmet_demand_and_feasibility_helpers() -> None:
    assert is_material_unmet_demand(0.0) is False
    assert is_material_unmet_demand(0.01) is True
    assert case_is_feasible("optimal") is True
    assert case_is_feasible("infeasible") is False
