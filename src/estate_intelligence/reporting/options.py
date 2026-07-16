"""Option catalogue construction."""

from __future__ import annotations

from typing import Any

from estate_intelligence.reporting.models import CommunicationOption


def build_options(
    config_options: list[dict[str, Any]],
    financial_rows: list[dict[str, Any]],
    scenario_rows: list[dict[str, Any]],
    optimisation_rows: list[dict[str, Any]],
) -> list[CommunicationOption]:
    financial_by_case = {str(row["financial_case_id"]): row for row in financial_rows}
    scenario_by_case = {str(row["scenario_id"]): row for row in scenario_rows}
    optimisation_by_case = {str(row["case_id"]): row for row in optimisation_rows}
    options: list[CommunicationOption] = []
    for config_option in config_options:
        source_case_id = str(config_option["source_case_id"])
        financial = financial_by_case[source_case_id]
        source = source_case_id.removeprefix("case_").split("_", 1)[1]
        feasibility = "descriptive_baseline"
        if source in scenario_by_case:
            feasibility = str(scenario_by_case[source]["feasibility_status"])
        if source in optimisation_by_case:
            feasibility = str(optimisation_by_case[source]["solver_status"])
        options.append(
            CommunicationOption(
                option_id=str(config_option["option_id"]),
                option_name=str(config_option["option_name"]),
                source_case_id=source_case_id,
                source_framework=str(config_option["source_framework"]),
                feasibility_status=feasibility,
                simulation_status="fail",
                financial_readiness=str(financial["readiness_status"]),
                nominal_npv=float(financial["npv"]),
                risk_adjusted_npv=float(financial["risk_adjusted_npv"]),
                payback_status=str(financial["simple_payback_year"]),
                key_operational_risk=(
                    "Linked simulation evidence failed configured resilience thresholds."
                ),
                key_financial_risk=(
                    "Nominal value is not realisable without operational mitigation."
                ),
                manual_review_required=1,
                implementation_status="not_approved",
            )
        )
    return options
