from pathlib import Path

from estate_intelligence.financial.models import FinanceConfig
from estate_intelligence.financial.sensitivity import sensitivity_rows, tornado_rows


def test_sensitivity_grid_and_tornado_ranking_are_deterministic() -> None:
    config = FinanceConfig.from_yaml(Path("config/finance.yaml"))

    rows = sensitivity_rows(
        financial_run_id="FIN-test",
        config=config,
        financial_case_id="case",
        baseline_recurring_cost=1000.0,
        case_recurring_cost=800.0,
        transition_cost=100.0,
        mitigation_cost=10.0,
        readiness_status="review_required",
        base_npv=100.0,
    )

    assert len(rows) == len(config.sensitivity_dimensions) * 3
    ranked = tornado_rows(rows)
    assert _as_float(ranked[0]["maximum_absolute_npv_impact"]) >= _as_float(
        ranked[-1]["maximum_absolute_npv_impact"]
    )


def _as_float(value: object) -> float:
    if isinstance(value, int | float | str):
        return float(value)
    raise TypeError(f"Expected numeric value, got {type(value)}")
