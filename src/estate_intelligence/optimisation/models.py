"""Typed configuration and evidence models for Milestone 8 optimisation."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field, field_validator


class OptimisationCase(BaseModel):
    case_id: str
    label: str
    allow_room_deactivation: bool
    allow_site_movement: bool
    allow_remote_delivery: bool


class PlanningDemandBasis(BaseModel):
    target: str
    interval_basis: str
    point_fallback: bool = True


class OptimisationConfig(BaseModel):
    contract_version: int
    milestone_owner: str
    framework_version: str
    purpose: str
    solver: str
    solver_time_limit_seconds: int = Field(gt=0)
    solver_mip_gap: float = Field(ge=0)
    solver_threads: int = Field(gt=0)
    analysis_horizon_months: int = Field(gt=0)
    source_run_requirements: dict[str, str]
    planning_demand_basis: PlanningDemandBasis
    allocation_grain: str
    candidate_source: dict[str, str]
    optimisation_cases: list[OptimisationCase]
    objective_weights: dict[str, float]
    cost_coefficients: dict[str, float]
    capacity_buffer: float = Field(ge=0, lt=1)
    contingency_capacity: float = Field(ge=0, lt=1)
    protected_capacity_policy: dict[str, bool]
    specialist_capacity_policy: dict[str, bool]
    room_compatibility_rules: dict[str, bool]
    service_continuity_rules: dict[str, float | bool]
    workforce_constraints: dict[str, float | bool]
    accessibility_constraints: dict[str, float]
    travel_penalty_rules: dict[str, float]
    co_location_rules: dict[str, bool]
    confidentiality_rules: dict[str, list[str]]
    remote_delivery_limits: dict[str, float | bool]
    building_activation_rules: dict[str, bool]
    room_activation_rules: dict[str, bool]
    relocation_rules: dict[str, int]
    disruption_penalties: dict[str, float]
    underutilisation_penalties: dict[str, bool]
    infeasibility_diagnostics: dict[str, bool]
    feasibility_statuses: list[str]
    evidence_output: dict[str, str | bool]
    rounding: dict[str, int]

    @field_validator("objective_weights", "cost_coefficients")
    @classmethod
    def non_negative_values(cls, values: dict[str, float]) -> dict[str, float]:
        if any(value < 0 for value in values.values()):
            raise ValueError("optimisation weights and coefficients must be non-negative")
        return values

    @classmethod
    def from_yaml(cls, path: Path) -> OptimisationConfig:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        return cls.model_validate(payload)


class Candidate(BaseModel):
    candidate_id: str
    service_id: str
    source_site_id: str
    target_site_id: str
    target_building_id: str
    target_room_id: str
    period: str
    planning_demand_hours: float
    compatible_capacity_hours: float
    room_type_compatible: bool
    equipment_compatible: bool
    capacity_compatible: bool
    accessibility_compatible: bool
    workforce_compatible: bool
    co_location_compatible: bool
    confidentiality_compatible: bool
    protected_capacity_effect: str
    travel_penalty: float
    relocation_penalty: float
    disruption_penalty: float
    candidate_status: str
    exclusion_reason: str

    @property
    def is_eligible(self) -> bool:
        return self.candidate_status == "eligible"


class DemandRow(BaseModel):
    service_id: str
    period: str
    point_demand_hours: float
    planning_demand_hours: float
    remote_eligible_rate: float
    source_site_id: str


class RoomCapacity(BaseModel):
    room_id: str
    building_id: str
    site_id: str
    monthly_capacity_hours: float
    allocatable_capacity_hours: float
    protected_capacity_flag: bool
    specialist_flag: bool


class SolverCaseResult(BaseModel):
    case_id: str
    solver_status: str
    native_status: str
    objective_value: float
    objective_gap: float
    allocated_demand_hours: float
    unmet_demand_hours: float
    remote_demand_hours: float
    active_rooms: int
    inactive_rooms: int
    active_buildings: int
    potentially_releasable_buildings: int
    services_moved: int
    solve_diagnostics: str


class OptimisationEvidence(BaseModel):
    candidates: list[dict[str, object]]
    variables: list[dict[str, object]]
    allocations: list[dict[str, object]]
    room_status: list[dict[str, object]]
    building_status: list[dict[str, object]]
    service_moves: list[dict[str, object]]
    constraints: list[dict[str, object]]
    binding_constraints: list[dict[str, object]]
    objective_components: list[dict[str, object]]
    solver_results: list[dict[str, object]]
    infeasibility: list[dict[str, object]]
    comparison: list[dict[str, object]]
