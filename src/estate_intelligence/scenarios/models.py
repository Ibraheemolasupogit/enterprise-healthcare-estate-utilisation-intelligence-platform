"""Typed models for deterministic scenario analysis."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, model_validator


class ScenarioDefinition(BaseModel):
    """Configured scenario catalogue item."""

    scenario_id: str
    scenario_type: Literal[
        "baseline", "light_consolidation", "site_consolidation", "hybrid_redesign"
    ]
    label: str


class ScenarioConfig(BaseModel):
    """Milestone 7 scenario configuration."""

    contract_version: int
    milestone_owner: str
    framework_version: str
    purpose: str
    analysis_horizon_months: int
    source_run_requirements: dict[str, str]
    scenario_catalogue: tuple[ScenarioDefinition, ...]
    capacity_buffer: float
    contingency_capacity: float
    forecast_demand_basis: str
    forecast_interval_basis: Literal["point", "upper_80", "upper_95"]
    room_compatibility_rules: dict[str, bool]
    specialist_capacity_policy: dict[str, bool]
    protected_capacity_policy: dict[str, bool]
    workforce_constraints: dict[str, float]
    accessibility_constraints: dict[str, float]
    travel_penalties: dict[str, float]
    co_location_rules: dict[str, bool]
    service_continuity_rules: dict[str, float | bool]
    building_eligibility_rules: dict[str, float | int | bool]
    cost_components: dict[str, object]
    implementation_burden_weights: dict[str, float]
    risk_thresholds: dict[str, float | int]
    feasibility_statuses: tuple[str, ...]
    scoring_weights: dict[str, float]
    evidence_output: dict[str, object]
    rounding: dict[str, int]

    @model_validator(mode="after")
    def weights_sum_to_one(self) -> ScenarioConfig:
        total = round(sum(self.scoring_weights.values()), 8)
        if total != 1.0:
            raise ValueError(f"scoring weights must sum to 1.0, got {total}")
        return self

    @classmethod
    def from_yaml(cls, path: Path) -> ScenarioConfig:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(document, dict):
            raise ValueError("scenario config must be a mapping")
        return cls.model_validate(document)
