from pathlib import Path

from estate_intelligence.financial.costs import recurring_cost_rows, transition_cost_rows
from estate_intelligence.financial.models import FinanceConfig, FinancialCase


def test_room_deactivation_does_not_remove_building_fixed_costs() -> None:
    config = FinanceConfig.from_yaml(Path("config/finance.yaml"))
    case = FinancialCase(
        financial_case_id="case_b",
        label="Light",
        source_type="scenario",
        source_case_id="light_consolidation",
        simulation_case_id="case_b_light_consolidation",
        released_buildings=[],
        retained_buildings=["BLD-001"],
        service_moves=2,
        remote_demand_hours=0.0,
        release_supported=False,
        release_statement="no building release",
    )

    rows = recurring_cost_rows(
        financial_run_id="FIN-test",
        config=config,
        case=case,
        building_costs={
            "BLD-001": {
                "lease_cost": 100.0,
                "maintenance_cost": 50.0,
                "utility_cost": 30.0,
                "security_cost": 20.0,
                "cleaning_cost": 10.0,
                "business_rates": 5.0,
                "exit_cost": 0.0,
            }
        },
    )

    lease = next(row for row in rows if row["cost_component"] == "lease_cost")
    assert lease["gross_recurring_cost_difference"] == 0.0
    assert lease["release_treatment"] == "retained_until_release"


def test_valid_building_release_removes_configured_recurring_costs() -> None:
    config = FinanceConfig.from_yaml(Path("config/finance.yaml"))
    case = FinancialCase(
        financial_case_id="case_e",
        label="Flexible room",
        source_type="optimisation",
        source_case_id="flexible_room",
        simulation_case_id="case_c_flexible_room_optimisation",
        released_buildings=["BLD-001"],
        retained_buildings=[],
        service_moves=1,
        remote_demand_hours=0.0,
        release_supported=True,
        release_statement="release supported",
    )

    rows = recurring_cost_rows(
        financial_run_id="FIN-test",
        config=config,
        case=case,
        building_costs={
            "BLD-001": {
                "lease_cost": 100.0,
                "maintenance_cost": 50.0,
                "utility_cost": 30.0,
                "security_cost": 20.0,
                "cleaning_cost": 10.0,
                "business_rates": 5.0,
                "exit_cost": 0.0,
            }
        },
    )

    assert sum(_as_float(row["gross_recurring_cost_difference"]) for row in rows) == 215.0


def test_transition_costs_include_lease_exit_and_refurbishment() -> None:
    config = FinanceConfig.from_yaml(Path("config/finance.yaml"))
    case = FinancialCase(
        financial_case_id="case_e",
        label="Flexible room",
        source_type="optimisation",
        source_case_id="flexible_room",
        simulation_case_id="case_c_flexible_room_optimisation",
        released_buildings=["BLD-001"],
        retained_buildings=["BLD-002"],
        service_moves=1,
        remote_demand_hours=0.0,
        release_supported=True,
        release_statement="release supported",
    )

    rows = transition_cost_rows(
        financial_run_id="FIN-test",
        config=config,
        case=case,
        released_recurring_cost=100000.0,
        curated_exit_cost=0.0,
    )

    lease_exit = next(row for row in rows if row["cost_component"] == "lease_exit_cost")
    refurbishment = next(row for row in rows if row["cost_component"] == "refurbishment_cost")
    assert _as_float(lease_exit["amount"]) > 0
    assert _as_float(refurbishment["amount"]) > 0


def _as_float(value: object) -> float:
    if isinstance(value, int | float | str):
        return float(value)
    raise TypeError(f"Expected numeric value, got {type(value)}")
