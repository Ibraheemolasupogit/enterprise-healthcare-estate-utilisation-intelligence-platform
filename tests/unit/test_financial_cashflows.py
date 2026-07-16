from pathlib import Path

from estate_intelligence.financial.cashflows import annual_cashflows, benefit_ramp
from estate_intelligence.financial.models import FinanceConfig


def test_cashflows_apply_benefit_ramp_and_escalation() -> None:
    config = FinanceConfig.from_yaml(Path("config/finance.yaml"))

    rows = annual_cashflows(
        config=config,
        assumption_name="base",
        assumption=config.base_case,
        financial_run_id="FIN-test",
        financial_case_id="case",
        baseline_recurring_cost=1000.0,
        case_recurring_cost=800.0,
        transition_cost=50.0,
        mitigation_cost=10.0,
    )

    assert benefit_ramp(config, 1, config.base_case) == 0.4
    assert rows[0]["gross_recurring_difference"] == 80.0
    assert rows[0]["transition_costs"] == 50.0
    assert _as_float(rows[1]["baseline_recurring_cost"]) > 1000.0


def _as_float(value: object) -> float:
    if isinstance(value, int | float | str):
        return float(value)
    raise TypeError(f"Expected numeric value, got {type(value)}")
