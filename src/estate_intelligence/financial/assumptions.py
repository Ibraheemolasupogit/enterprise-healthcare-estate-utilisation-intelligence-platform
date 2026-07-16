"""Financial assumption export helpers."""

from __future__ import annotations

from estate_intelligence.financial.models import FinanceConfig


def assumption_rows(financial_run_id: str, config: FinanceConfig) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    scalar_assumptions: dict[str, str] = {
        "currency": config.currency,
        "price_basis": config.price_basis,
        "analysis_start_period": config.analysis_start_period,
        "analysis_horizon_years": str(config.analysis_horizon_years),
        "discount_rate": str(config.discount_rate),
        "inflation_rate": str(config.inflation_rate),
        "annual_cost_escalation": str(config.annual_cost_escalation),
    }
    for name, value in sorted(scalar_assumptions.items()):
        rows.append(
            {
                "financial_run_id": financial_run_id,
                "assumption_set": "framework",
                "assumption_name": name,
                "assumption_value": value,
                "evidence_source": "config/finance.yaml",
            }
        )
    for ramp_name, ramp_value in sorted(config.benefit_ramp.items()):
        rows.append(
            {
                "financial_run_id": financial_run_id,
                "assumption_set": "benefit_ramp",
                "assumption_name": ramp_name,
                "assumption_value": str(ramp_value),
                "evidence_source": "config/finance.yaml",
            }
        )
    for component, settings in sorted(config.recurring_cost_components.items()):
        rows.append(
            {
                "financial_run_id": financial_run_id,
                "assumption_set": "recurring_cost_components",
                "assumption_name": component,
                "assumption_value": settings.model_dump_json(),
                "evidence_source": "config/finance.yaml",
            }
        )
    for case_name in ("optimistic_case", "base_case", "pessimistic_case"):
        case_value = getattr(config, case_name)
        rows.append(
            {
                "financial_run_id": financial_run_id,
                "assumption_set": "case_assumptions",
                "assumption_name": case_name,
                "assumption_value": case_value.model_dump_json(),
                "evidence_source": "config/finance.yaml",
            }
        )
    return rows
