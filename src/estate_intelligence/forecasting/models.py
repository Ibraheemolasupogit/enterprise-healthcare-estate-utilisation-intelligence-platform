"""Typed models for deterministic demand forecasting."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, model_validator

EligibilityStatus = Literal[
    "eligible",
    "baseline_only",
    "insufficient_history",
    "too_sparse",
    "constant_series",
    "quality_blocked",
    "inactive_series",
]


class ModelSpec(BaseModel):
    """Configured forecasting model."""

    model_id: str
    model_type: str
    parameters: dict[str, float | int | str | bool] = Field(default_factory=dict)
    minimum_periods: int = 1
    requires_seasonality: bool = False
    requires_non_constant: bool = False


class SeriesDefinition(BaseModel):
    """Configured forecast series definition."""

    target: str
    entity_type: Literal["estate", "service"]
    source: Literal["activity", "workforce"]
    measure: str
    unit: str
    optional: bool = False


class ForecastingConfig(BaseModel):
    """Milestone 6 forecasting configuration."""

    contract_version: int
    milestone_owner: str
    framework_version: str
    purpose: str
    reference_date: str
    forecast_grain: Literal["month"]
    forecast_horizon: int
    minimum_history_periods: int
    minimum_non_zero_periods: int
    maximum_missing_period_ratio: float
    intermittency_thresholds: dict[str, float]
    validation_strategy: Literal["expanding_window"]
    initial_training_periods: int
    validation_horizon: int
    rolling_step: int
    model_catalogue: tuple[ModelSpec, ...]
    selection_metric: str
    secondary_metrics: tuple[str, ...]
    prediction_interval_levels: tuple[float, ...]
    seasonal_period: int
    series_definitions: tuple[SeriesDefinition, ...]
    fallback_policy: dict[str, str]
    evidence_output: dict[str, object]
    rounding: dict[str, int]

    @model_validator(mode="after")
    def validate_windows(self) -> ForecastingConfig:
        if self.forecast_horizon < 1:
            raise ValueError("forecast_horizon must be positive")
        if self.initial_training_periods < self.minimum_history_periods:
            raise ValueError("initial_training_periods must meet minimum_history_periods")
        if self.validation_horizon < 1 or self.rolling_step < 1:
            raise ValueError("validation_horizon and rolling_step must be positive")
        if not self.model_catalogue:
            raise ValueError("model_catalogue must not be empty")
        return self

    @classmethod
    def from_yaml(cls, path: Path) -> ForecastingConfig:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(document, dict):
            raise ValueError("forecasting config must be a mapping")
        return cls.model_validate(document)


@dataclass(frozen=True)
class SeriesPoint:
    """One period in a constructed forecast series."""

    series_id: str
    target: str
    entity_type: str
    entity_id: str
    period: str
    value: float
    observation_count: int
    quality_flag: str
    imputation_flag: str
    source_run_ids: str


@dataclass(frozen=True)
class ForecastSeries:
    """A complete monthly series."""

    series_id: str
    target: str
    entity_type: str
    entity_id: str
    points: tuple[SeriesPoint, ...]

    @property
    def values(self) -> list[float]:
        return [point.value for point in self.points]

    @property
    def periods(self) -> list[str]:
        return [point.period for point in self.points]


@dataclass(frozen=True)
class EligibilityResult:
    """Forecast eligibility result and diagnostics."""

    series_id: str
    target: str
    entity_type: str
    entity_id: str
    eligibility_status: EligibilityStatus
    reason: str
    historical_periods: int
    non_zero_periods: int
    missing_period_ratio: float
    variance: float
    non_zero_ratio: float
    average_interval_between_non_zero_periods: float | None
    squared_coefficient_of_variation: float | None
    recent_activity_flag: bool


@dataclass(frozen=True)
class Fold:
    """Chronological validation fold."""

    fold_id: str
    fold_number: int
    train_start: int
    train_end: int
    validation_start: int
    validation_end: int


@dataclass(frozen=True)
class ModelResult:
    """Aggregated model validation result."""

    model_id: str
    parameters: dict[str, Any]
    forecasts: tuple[float, ...]
    actuals: tuple[float, ...]
    evaluated_fold_count: int
    metrics: dict[str, float | None]
    model_status: str


@dataclass(frozen=True)
class SelectionResult:
    """Selected model evidence."""

    series_id: str
    selected_model_id: str
    primary_metric: str
    primary_metric_value: float | None
    baseline_model_id: str
    baseline_metric_value: float | None
    baseline_beaten_flag: bool
    selection_reason: str
