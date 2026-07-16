"""Typed models for Milestone 10 financial analysis."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator


class FinancialCaseConfig(BaseModel):
    financial_case_id: str
    label: str
    source_type: str
    source_case_id: str
    simulation_case_id: str


class RecurringComponentConfig(BaseModel):
    classification: str
    release_allowed: bool
    variable_fraction: float = Field(ge=0.0, le=1.0)
    retained_floor_fraction: float = Field(default=0.0, ge=0.0, le=1.0)


class TransitionComponentConfig(BaseModel):
    coefficient: float | None = None
    coefficient_per_service_move: float | None = None
    coefficient_per_released_building: float | None = None
    coefficient_per_retained_building: float | None = None
    coefficient_per_remote_hour: float | None = None
    coefficient_per_case: float | None = None
    coefficient_of_released_recurring_cost: float | None = None
    coefficient_of_transition_subtotal: float | None = None
    minimum_case_cost: float = 0.0
    timing_year: int = Field(ge=0)
    uncertainty_low: float = Field(gt=0)
    uncertainty_high: float = Field(gt=0)


class MitigationComponentConfig(BaseModel):
    annual_cost_per_blocked_contact: float | None = None
    annual_cost_per_workforce_bottleneck: float | None = None
    annual_cost_per_overtime_hour: float | None = None
    annual_case_cost: float | None = None
    applies_to_failure_types: list[str]


class SensitivityDimension(BaseModel):
    low: float
    base: float
    high: float


class AssumptionSetConfig(BaseModel):
    implementation_cost_multiplier: float = Field(gt=0)
    transition_cost_multiplier: float = Field(gt=0)
    mitigation_cost_multiplier: float = Field(ge=0)
    benefit_ramp_multiplier: float = Field(gt=0)
    demand_growth_rate: float = Field(ge=0)
    release_delay_years: int = Field(ge=0)


class FinanceConfig(BaseModel):
    contract_version: int
    milestone_owner: str
    framework_version: str
    purpose: str
    currency: str
    price_basis: str
    analysis_start_period: str
    analysis_horizon_years: int = Field(gt=0)
    discount_rate: float = Field(ge=0)
    inflation_rate: float = Field(ge=0)
    annual_cost_escalation: float = Field(ge=0)
    benefit_ramp: dict[str, float]
    implementation_phasing: dict[str, float | int]
    source_run_requirements: dict[str, str]
    financial_case_catalogue: list[FinancialCaseConfig]
    recurring_cost_components: dict[str, RecurringComponentConfig]
    excluded_recurring_components: list[str]
    transition_cost_components: dict[str, TransitionComponentConfig]
    lease_exit_rules: dict[str, Any]
    relocation_cost_rules: dict[str, Any]
    refurbishment_cost_rules: dict[str, Any]
    technology_enablement_rules: dict[str, Any]
    transition_staffing_rules: dict[str, Any]
    operational_mitigation_costs: dict[str, MitigationComponentConfig]
    simulation_risk_adjustments: dict[str, float]
    forecast_uncertainty_adjustments: dict[str, float]
    demand_growth_assumptions: dict[str, float]
    residual_value_policy: dict[str, float | bool]
    payback_policy: dict[str, str | bool]
    npv_policy: dict[str, str | bool]
    sensitivity_dimensions: dict[str, SensitivityDimension]
    optimistic_case: AssumptionSetConfig
    base_case: AssumptionSetConfig
    pessimistic_case: AssumptionSetConfig
    break_even_parameters: dict[str, float | int]
    confidence_thresholds: dict[str, float]
    evidence_output: dict[str, str | bool]
    rounding: dict[str, int]

    @field_validator("milestone_owner")
    @classmethod
    def milestone_must_be_ten(cls, value: str) -> str:
        if value != "Milestone 10":
            raise ValueError("finance configuration must be owned by Milestone 10")
        return value

    @classmethod
    def from_yaml(cls, path: Path) -> FinanceConfig:
        return cls.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


class FinancialCase(BaseModel):
    financial_case_id: str
    label: str
    source_type: str
    source_case_id: str
    simulation_case_id: str
    released_buildings: list[str]
    retained_buildings: list[str]
    service_moves: int
    remote_demand_hours: float
    release_supported: bool
    release_statement: str


class FinanceEvidence(BaseModel):
    cases: list[dict[str, object]]
    assumptions: list[dict[str, object]]
    recurring_costs: list[dict[str, object]]
    transition_costs: list[dict[str, object]]
    mitigation_costs: list[dict[str, object]]
    cashflows: list[dict[str, object]]
    payback: list[dict[str, object]]
    npv: list[dict[str, object]]
    cumulative_effects: list[dict[str, object]]
    sensitivity: list[dict[str, object]]
    break_even: list[dict[str, object]]
    risk_adjustments: list[dict[str, object]]
    confidence: list[dict[str, object]]
    comparison: list[dict[str, object]]
