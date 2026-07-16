"""Deterministic financial sensitivity analysis."""

from __future__ import annotations

from copy import deepcopy

from estate_intelligence.financial.cashflows import annual_cashflows
from estate_intelligence.financial.models import FinanceConfig
from estate_intelligence.financial.npv import net_present_value


def sensitivity_rows(
    *,
    financial_run_id: str,
    config: FinanceConfig,
    financial_case_id: str,
    baseline_recurring_cost: float,
    case_recurring_cost: float,
    transition_cost: float,
    mitigation_cost: float,
    readiness_status: str,
    base_npv: float,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for parameter, dimension in sorted(config.sensitivity_dimensions.items()):
        for level in ("low", "base", "high"):
            value = float(getattr(dimension, level))
            assumption = deepcopy(config.base_case)
            adjusted_transition = transition_cost
            adjusted_mitigation = mitigation_cost
            adjusted_case_cost = case_recurring_cost
            if parameter in {"implementation_cost", "transition_cost"}:
                adjusted_transition = transition_cost * value
            elif parameter == "operational_mitigation_cost":
                adjusted_mitigation = mitigation_cost * value
            elif parameter == "benefit_ramp":
                assumption = assumption.model_copy(update={"benefit_ramp_multiplier": value})
            elif parameter == "discount_rate":
                config_rate = value
            else:
                config_rate = config.discount_rate
            if parameter == "demand_growth":
                assumption = assumption.model_copy(update={"demand_growth_rate": value})
            if parameter == "building_release_timing":
                assumption = assumption.model_copy(update={"release_delay_years": int(value)})
            if parameter == "cost_escalation":
                working = config.model_copy(update={"annual_cost_escalation": value})
            else:
                working = config
            if parameter != "discount_rate":
                config_rate = working.discount_rate
            cashflows = annual_cashflows(
                config=working,
                assumption_name="sensitivity",
                assumption=assumption,
                financial_run_id=financial_run_id,
                financial_case_id=financial_case_id,
                baseline_recurring_cost=baseline_recurring_cost,
                case_recurring_cost=adjusted_case_cost,
                transition_cost=adjusted_transition,
                mitigation_cost=adjusted_mitigation,
            )
            values = [_as_float(row["net_annual_financial_effect"]) for row in cashflows]
            npv = net_present_value(values, config_rate)
            rows.append(
                {
                    "financial_run_id": financial_run_id,
                    "financial_case_id": financial_case_id,
                    "sensitivity_parameter": parameter,
                    "sensitivity_level": level,
                    "sensitivity_value": round(value, 4),
                    "npv": round(npv, 4),
                    "five_year_cumulative_effect": round(sum(values), 4),
                    "readiness_status": readiness_status,
                    "tornado_impact": round(abs(npv - base_npv), 4),
                }
            )
    return rows


def tornado_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str], float] = {}
    for row in rows:
        key = (str(row["financial_case_id"]), str(row["sensitivity_parameter"]))
        grouped[key] = max(grouped.get(key, 0.0), _as_float(row["tornado_impact"]))
    ranked = []
    for rank, ((case_id, parameter), impact) in enumerate(
        sorted(grouped.items(), key=lambda item: (-item[1], item[0][0], item[0][1])),
        start=1,
    ):
        ranked.append(
            {
                "financial_case_id": case_id,
                "sensitivity_parameter": parameter,
                "rank": rank,
                "maximum_absolute_npv_impact": round(impact, 4),
            }
        )
    return ranked


def _as_float(value: object) -> float:
    if isinstance(value, int | float | str):
        return float(value)
    raise TypeError(f"Expected numeric financial value, got {type(value)}")
