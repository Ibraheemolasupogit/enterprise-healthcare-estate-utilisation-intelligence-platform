"""Typed data-quality rule and result models."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Dimension = Literal[
    "completeness",
    "validity",
    "consistency",
    "uniqueness",
    "timeliness",
    "referential_integrity",
    "reconciliation",
]
Severity = Literal["info", "warning", "high", "critical"]
FailureAction = Literal["accept", "accept_with_warning", "manual_review", "reject"]


class QualityRule(BaseModel):
    """Configured and typed quality rule."""

    model_config = ConfigDict(frozen=True)

    rule_id: str = Field(pattern=r"^DQ-[A-Z]{3}-[A-Z]{3}-\d{3}$")
    rule_name: str
    dataset: str
    dimension: Dimension
    description: str
    severity: Severity
    field_names: tuple[str, ...]
    scope: str
    threshold: str
    enabled: bool = True
    expected_outcome: str
    failure_action: FailureAction
    downstream_impact: str
    milestone_owner: str = "Milestone 4"


class QualityIssue(BaseModel):
    """Record-level quality issue."""

    evidence_key: str
    rule_id: str
    dataset: str
    record_identifier: str
    field_name: str
    observed_value: str | None
    expected_condition: str
    severity: Severity
    failure_action: FailureAction
    status: str
    issue_description: str
    source_file: str | None = None
    source_row_number: int | None = None
    intentional_issue_id: str | None = None
