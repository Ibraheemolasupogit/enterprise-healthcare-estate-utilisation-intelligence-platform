"""Annual cash-flow calculations."""

from __future__ import annotations

from estate_intelligence.financial.models import AssumptionSetConfig, FinanceConfig
from estate_intelligence.financial.npv import discount_factor


def benefit_ramp(config: FinanceConfig, year: int, assumption: AssumptionSetConfig) -> float:
    if year <= int(assumption.release_delay_years):
        return 0.0
    adjusted_year = year - int(assumption.release_delay_years)
    if adjusted_year == 1:
        base = float(config.benefit_ramp["year_1"])
    elif adjusted_year == 2:
        base = float(config.benefit_ramp["year_2"])
    else:
        base = float(config.benefit_ramp["year_3_plus"])
    return min(1.0, base * assumption.benefit_ramp_multiplier)


def annual_cashflows(
    *,
    config: FinanceConfig,
    assumption_name: str,
    assumption: AssumptionSetConfig,
    financial_run_id: str,
    financial_case_id: str,
    baseline_recurring_cost: float,
    case_recurring_cost: float,
    transition_cost: float,
    mitigation_cost: float,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    cumulative = 0.0
    gross_difference = baseline_recurring_cost - case_recurring_cost
    for year in range(1, config.analysis_horizon_years + 1):
        escalation = (1.0 + config.annual_cost_escalation) ** (year - 1)
        growth = (1.0 + assumption.demand_growth_rate) ** (year - 1)
        ramp = benefit_ramp(config, year, assumption)
        baseline = baseline_recurring_cost * escalation * growth
        case_cost = baseline - (gross_difference * escalation * ramp)
        transition = transition_cost * assumption.transition_cost_multiplier if year == 1 else 0.0
        implementation = 0.0
        mitigation = mitigation_cost * assumption.mitigation_cost_multiplier * escalation * growth
        net_effect = (baseline - case_cost) - transition - mitigation - implementation
        cumulative += net_effect
        factor = discount_factor(config.discount_rate, year)
        rows.append(
            {
                "financial_run_id": financial_run_id,
                "financial_case_id": financial_case_id,
                "assumption_set": assumption_name,
                "analysis_year": year,
                "baseline_recurring_cost": round(baseline, 4),
                "case_recurring_cost": round(case_cost, 4),
                "gross_recurring_difference": round(baseline - case_cost, 4),
                "transition_costs": round(transition, 4),
                "mitigation_costs": round(mitigation, 4),
                "implementation_costs": round(implementation, 4),
                "net_annual_financial_effect": round(net_effect, 4),
                "discount_factor": round(factor, 8),
                "discounted_cash_flow": round(net_effect * factor, 4),
                "cumulative_cash_flow": round(cumulative, 4),
            }
        )
    return rows
