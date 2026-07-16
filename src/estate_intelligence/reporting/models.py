"""Typed structures for communication and governance evidence."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CommunicationConfig:
    framework_version: str
    document: dict[str, Any]
    config_path: Path


@dataclass(frozen=True)
class Audience:
    audience_id: str
    label: str
    detail_level: str
    primary_need: str


@dataclass(frozen=True)
class CommunicationOption:
    option_id: str
    option_name: str
    source_case_id: str
    source_framework: str
    feasibility_status: str
    simulation_status: str
    financial_readiness: str
    nominal_npv: float
    risk_adjusted_npv: float
    payback_status: str
    key_operational_risk: str
    key_financial_risk: str
    manual_review_required: int
    implementation_status: str


@dataclass(frozen=True)
class Objection:
    objection_id: str
    stakeholder_group: str
    objection_summary: str
    evidence_required: str
    source_evidence: str
    status: str
    analysis_response: str
    decision_impact: str
    revision_required: int
    scenario_label: str = "synthetic challenge scenario"


@dataclass(frozen=True)
class ChallengeResponse:
    challenge_id: str
    objection_id: str
    support_status: str
    evidence_considered: str
    analytical_response: str
    conclusion_change: str
    unresolved_concern: str


@dataclass(frozen=True)
class Revision:
    revision_id: str
    initial_position: str
    challenge_id: str
    evidence_considered: str
    revised_position: str
    reason_for_change: str
    affected_outputs: str
    status: str


@dataclass(frozen=True)
class Claim:
    claim_id: str
    audience: str
    claim_summary: str
    source_table: str
    source_run_id: str
    source_record_or_metric: str
    interpretation_rule: str
    caveat: str
    output_document: str


@dataclass(frozen=True)
class CommunicationRun:
    communication_run_id: str
    lineage: dict[str, str]
    config_checksum: str
    audience_catalogue_checksum: str
    option_catalogue_checksum: str
    challenge_catalogue_checksum: str
    decision_status: str
    approval_status: str
