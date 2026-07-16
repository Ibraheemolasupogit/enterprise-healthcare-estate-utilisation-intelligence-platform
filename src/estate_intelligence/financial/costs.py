"""Financial cost calculations."""

from __future__ import annotations

from collections.abc import Iterable

from estate_intelligence.financial.models import FinanceConfig, FinancialCase


def recurring_cost_rows(
    *,
    financial_run_id: str,
    config: FinanceConfig,
    case: FinancialCase,
    building_costs: dict[str, dict[str, float]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    released = set(case.released_buildings) if case.release_supported else set()
    for component, settings in sorted(config.recurring_cost_components.items()):
        baseline = sum(costs[component] for costs in building_costs.values())
        removed = sum(building_costs[building][component] for building in released)
        case_amount = baseline - removed
        treatment = "released_building_cost_removed" if removed else "retained_until_release"
        if settings.classification == "variable" and not released:
            treatment = "variable_component_retained_no_release"
        if settings.classification == "semi_variable" and released:
            treatment = "released_building_component_removed_with_floor_for_retained_estate"
        rows.append(
            {
                "financial_run_id": financial_run_id,
                "financial_case_id": case.financial_case_id,
                "cost_component": component,
                "baseline_amount": round(baseline, 4),
                "case_amount": round(case_amount, 4),
                "gross_recurring_cost_difference": round(baseline - case_amount, 4),
                "classification": settings.classification,
                "release_treatment": treatment,
                "evidence_source": "curated_finance_and_financial_release_conditions",
            }
        )
    return rows


def transition_cost_rows(
    *,
    financial_run_id: str,
    config: FinanceConfig,
    case: FinancialCase,
    released_recurring_cost: float,
    curated_exit_cost: float,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    released_count = len(case.released_buildings)
    retained_count = len(case.retained_buildings)
    subtotal = 0.0
    for component, settings in sorted(config.transition_cost_components.items()):
        amount = 0.0
        formula = "configured coefficient"
        coefficient = 0.0
        if component == "lease_exit_cost":
            coefficient = float(settings.coefficient or 0.0)
            amount = (
                max(curated_exit_cost, released_recurring_cost * coefficient)
                if released_count
                else 0.0
            )
            formula = "max(curated_exit_cost, released_recurring_cost * coefficient)"
        elif component == "relocation_cost":
            coefficient = float(settings.coefficient_per_service_move or 0.0)
            amount = case.service_moves * coefficient + released_count * float(
                settings.coefficient_per_released_building or 0.0
            )
            formula = "service_moves * coefficient + released_buildings * release_coefficient"
        elif component == "refurbishment_cost":
            coefficient = float(settings.coefficient_per_retained_building or 0.0)
            amount = retained_count * coefficient * float(
                config.refurbishment_cost_rules["retained_building_fraction"]
            ) + released_count * float(settings.coefficient_per_released_building or 0.0)
            formula = (
                "retained_buildings * coefficient * retained_fraction "
                "+ released_buildings * release_coefficient"
            )
        elif component == "technology_enablement_cost":
            coefficient = float(settings.coefficient_per_remote_hour or 0.0)
            if case.remote_demand_hours > 0:
                amount = max(settings.minimum_case_cost, case.remote_demand_hours * coefficient)
            formula = "max(minimum_case_cost, remote_demand_hours * coefficient)"
        elif component == "transition_staffing_cost":
            coefficient = float(settings.coefficient_per_service_move or 0.0)
            amount = case.service_moves * coefficient + released_count * float(
                settings.coefficient_per_released_building or 0.0
            )
            formula = "service_moves * coefficient + released_buildings * release_coefficient"
        elif component == "change_management_cost":
            coefficient = float(settings.coefficient_per_case or 0.0)
            amount = coefficient if case.source_type != "baseline" else 0.0
            formula = "coefficient_per_case for non-baseline cases"
        elif component == "temporary_dual_running_cost":
            coefficient = float(settings.coefficient_of_released_recurring_cost or 0.0)
            amount = released_recurring_cost * coefficient
            formula = "released_recurring_cost * coefficient"
        elif component == "contingency_cost":
            coefficient = float(settings.coefficient_of_transition_subtotal or 0.0)
            amount = subtotal * coefficient
            formula = "transition_subtotal * coefficient"
        subtotal += amount
        rows.append(
            {
                "financial_run_id": financial_run_id,
                "financial_case_id": case.financial_case_id,
                "cost_component": component,
                "amount": round(amount, 4),
                "timing_year": settings.timing_year,
                "trigger": "released_buildings_or_service_moves_or_remote_enablement",
                "formula": formula,
                "coefficient": round(coefficient, 4),
                "uncertainty_low": settings.uncertainty_low,
                "uncertainty_high": settings.uncertainty_high,
                "evidence_source": "curated_finance_scenario_optimisation_and_config",
                "inclusion_reason": "explicit configured Milestone 10 transition exposure",
            }
        )
    return rows


def total_amount(rows: Iterable[dict[str, object]], column: str = "amount") -> float:
    return sum(_as_float(row[column]) for row in rows)


def _as_float(value: object) -> float:
    if isinstance(value, int | float | str):
        return float(value)
    raise TypeError(f"Expected numeric financial value, got {type(value)}")
