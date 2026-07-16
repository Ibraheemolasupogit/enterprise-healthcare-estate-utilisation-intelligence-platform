"""Typed assurance models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

AssuranceStatus = Literal["pass", "pass_with_warnings", "fail", "not_applicable", "not_run"]
GateStatus = Literal["pass", "conditional_pass", "fail", "not_evaluated"]


@dataclass(frozen=True)
class AssuranceCheck:
    check_id: str
    category: str
    name: str
    description: str
    severity: str
    required: bool
    command_or_method: str
    expected_condition: str
    failure_action: str
    evidence_source: str


@dataclass(frozen=True)
class AssuranceResult:
    check: AssuranceCheck
    status: AssuranceStatus
    observed_result: str
    checksum: str


@dataclass(frozen=True)
class ReleaseGate:
    gate_id: str
    gate_name: str
    status: GateStatus
    conditions: str
    evidence_source: str
