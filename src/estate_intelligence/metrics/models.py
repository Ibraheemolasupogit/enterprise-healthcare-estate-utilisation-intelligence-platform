"""Typed models for deterministic utilisation analytics."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, model_validator


class TimeBand(BaseModel):
    """Configured non-overlapping time band."""

    start: str
    end: str
    peak: bool


class QualityPolicy(BaseModel):
    """Quality-gating policy for analytical populations."""

    allowed_record_statuses: tuple[str, ...]
    include_accepted_with_warning: bool
    manual_review: dict[str, Literal["exclude", "include"]]
    rejected: Literal["exclude", "include"]


class UtilisationConfig(BaseModel):
    """Milestone 5 utilisation configuration."""

    contract_version: int
    milestone_owner: str
    framework_version: str
    purpose: str
    quality_policy: QualityPolicy
    working_days: tuple[str, ...]
    analysis_period: dict[str, str]
    standard_opening: dict[str, str]
    time_bands: dict[str, TimeBand]
    formula_weights: dict[str, float]
    thresholds: dict[str, float]
    specialist_capacity: dict[str, object]
    cost_allocation: dict[str, tuple[str, ...]]
    rounding: dict[str, int]
    output: dict[str, object]

    @model_validator(mode="after")
    def weights_sum_to_one(self) -> UtilisationConfig:
        total = round(sum(self.formula_weights.values()), 8)
        if total != 1.0:
            raise ValueError(f"formula weights must sum to 1.0, got {total}")
        return self

    @classmethod
    def from_yaml(cls, path: Path) -> UtilisationConfig:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(document, dict):
            raise ValueError("utilisation config must be a mapping")
        return cls.model_validate(document)


class MetricResult(BaseModel):
    """Generic metric value for formula-level tests."""

    formula_id: str
    numerator: float
    denominator: float
    value: float = Field(ge=0.0)
