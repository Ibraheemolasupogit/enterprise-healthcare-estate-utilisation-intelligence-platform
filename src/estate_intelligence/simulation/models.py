"""Typed models for Milestone 9 simulation."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field, field_validator


class SimulationExperiment(BaseModel):
    experiment_id: str
    label: str
    demand_multiplier: float = Field(gt=0)
    workforce_multiplier: float = Field(gt=0)
    duration_multiplier: float = Field(gt=0)
    specialist_room_capacity_multiplier: float = Field(gt=0, le=1)


class SimulationConfig(BaseModel):
    contract_version: int
    milestone_owner: str
    framework_version: str
    purpose: str
    engine: str
    engine_version: str
    master_seed: int
    replications: int = Field(gt=0)
    warm_up_period: int = Field(ge=0)
    simulation_horizon: int = Field(gt=0)
    time_unit: str
    working_days_per_month: int = Field(gt=0)
    source_run_requirements: dict[str, str]
    allocation_sources: dict[str, str]
    experiment_catalogue: list[SimulationExperiment]
    arrival_process: dict[str, str | int | float]
    service_time_distributions: dict[str, object]
    cancellation_rules: dict[str, bool | float]
    no_show_rules: dict[str, bool | float]
    late_start_rules: dict[str, bool | float]
    session_overrun_rules: dict[str, int | float]
    workforce_availability: dict[str, str | int | float]
    room_capacity: dict[str, str | float]
    priority_rules: dict[str, str | bool]
    queue_discipline: str
    contingency_policy: dict[str, float]
    demand_shocks: dict[str, float]
    workforce_shocks: dict[str, float]
    duration_shocks: dict[str, float]
    equipment_downtime: dict[str, float]
    performance_thresholds: dict[str, float | int]
    confidence_interval: dict[str, float | str]
    evidence_output: dict[str, str | bool]
    rounding: dict[str, int]

    @field_validator("milestone_owner")
    @classmethod
    def milestone_must_be_nine(cls, value: str) -> str:
        if value != "Milestone 9":
            raise ValueError("simulation configuration must be owned by Milestone 9")
        return value

    @field_validator("queue_discipline")
    @classmethod
    def queue_must_be_fifo(cls, value: str) -> str:
        if value != "fifo":
            raise ValueError("only fifo queue discipline is currently supported")
        return value

    @classmethod
    def from_yaml(cls, path: Path) -> SimulationConfig:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        return cls.model_validate(payload)


class RoomInput(BaseModel):
    room_id: str
    building_id: str
    site_id: str
    room_type: str
    capacity: int
    specialist_equipment: str
    protected_capacity_flag: bool
    specialist_flag: bool
    opening_minute: int
    closing_minute: int


class ServiceInput(BaseModel):
    service_id: str
    service_name: str
    minimum_room_type: str
    specialist_equipment_required: str
    remote_eligible_rate: float
    average_duration_minutes: float


class AllocationInput(BaseModel):
    simulation_case_id: str
    service_id: str
    period: str
    room_id: str
    building_id: str
    site_id: str
    allocated_hours: float
    remote_hours: float = 0.0


class SimulationCase(BaseModel):
    simulation_case_id: str
    source_type: str
    source_case_id: str
    label: str
    allocations: list[AllocationInput]
    active_room_ids: set[str]

    @property
    def active_rooms(self) -> int:
        return len(self.active_room_ids)


class Arrival(BaseModel):
    sequence: int
    service_id: str
    room_id: str
    arrival_minute: float
    duration_minutes: float
    cancelled: bool
    no_show: bool


class ContactEvent(BaseModel):
    sequence: int
    event_type: str
    event_time: float
    service_id: str
    room_id: str
    wait_minutes: float
    service_duration_minutes: float
    completion_status: str


class ReplicationResult(BaseModel):
    simulation_case_id: str
    experiment_id: str
    replication: int
    replication_seed: int
    events: list[ContactEvent]
    room_rows: list[dict[str, object]]
    service_rows: list[dict[str, object]]
    queue_rows: list[dict[str, object]]
    workforce_rows: list[dict[str, object]]
    arrivals: int
    completed_contacts: int
    unserved_contacts: int
    completion_rate: float
    mean_wait_minutes: float
    p95_wait_minutes: float
    room_contention_events: int
    workforce_blocked_contacts: int
    status: str


class SimulationEvidence(BaseModel):
    cases: list[dict[str, object]]
    experiments: list[dict[str, object]]
    replications: list[dict[str, object]]
    events: list[dict[str, object]]
    resource_metrics: list[dict[str, object]]
    service_metrics: list[dict[str, object]]
    queue_metrics: list[dict[str, object]]
    workforce_metrics: list[dict[str, object]]
    resilience_metrics: list[dict[str, object]]
    threshold_results: list[dict[str, object]]
    summary: list[dict[str, object]]
    failures: list[dict[str, object]]
