"""Milestone 4 deterministic data-quality rule catalogue."""

from __future__ import annotations

import hashlib
import json

from estate_intelligence.validation.models import Dimension, QualityRule

DATASETS = (
    "buildings",
    "rooms",
    "services",
    "bookings",
    "clinical_activity",
    "workforce",
    "finance",
    "accessibility",
)
DIMENSIONS: tuple[Dimension, ...] = (
    "completeness",
    "validity",
    "consistency",
    "uniqueness",
    "timeliness",
    "referential_integrity",
    "reconciliation",
)

SPECIAL_RULES = {
    ("rooms", "uniqueness"): ("DQ-ROM-UNI-001", "Duplicate room names", "warning", "manual_review"),
    ("rooms", "completeness"): (
        "DQ-ROM-CMP-001",
        "Specialist equipment completeness",
        "warning",
        "accept_with_warning",
    ),
    ("bookings", "consistency"): (
        "DQ-BKG-CON-001",
        "Attendance does not exceed planned",
        "high",
        "manual_review",
    ),
    ("finance", "consistency"): (
        "DQ-FIN-CON-001",
        "Lease cost aligns to ownership",
        "high",
        "manual_review",
    ),
    ("workforce", "consistency"): (
        "DQ-WRK-CON-001",
        "Available FTE within planned FTE",
        "warning",
        "accept_with_warning",
    ),
}


def build_rule_catalogue() -> list[QualityRule]:
    """Build stable rules for every dataset and quality dimension."""

    rules: list[QualityRule] = []
    for dataset in DATASETS:
        prefix = _prefix(dataset)
        for dimension in DIMENSIONS:
            special = SPECIAL_RULES.get((dataset, dimension))
            if special:
                rule_id, name, severity, action = special
            else:
                rule_id = f"DQ-{prefix}-{_dimension_code(dimension)}-001"
                name = f"{dataset} {dimension} control"
                severity = "warning" if dimension in {"timeliness", "reconciliation"} else "info"
                action = "accept_with_warning" if severity == "warning" else "accept"
            rules.append(
                QualityRule(
                    rule_id=rule_id,
                    rule_name=name,
                    dataset=dataset,
                    dimension=dimension,
                    description=f"Deterministic {dimension} quality rule for {dataset}.",
                    severity=severity,  # type: ignore[arg-type]
                    field_names=_fields(dataset, dimension),
                    scope="record" if dimension != "reconciliation" else "dataset",
                    threshold="configured",
                    enabled=True,
                    expected_outcome="no unexpected failures",
                    failure_action=action,  # type: ignore[arg-type]
                    downstream_impact=(
                        "Controls readiness for later analytics without calculating metrics."
                    ),
                )
            )
    return sorted(rules, key=lambda rule: rule.rule_id)


def rule_catalogue_checksum(rules: list[QualityRule]) -> str:
    """Return a stable checksum for the rule catalogue."""

    payload = [rule.model_dump(mode="json") for rule in rules]
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def _prefix(dataset: str) -> str:
    return {
        "buildings": "BLD",
        "rooms": "ROM",
        "services": "SVC",
        "bookings": "BKG",
        "clinical_activity": "ACT",
        "workforce": "WRK",
        "finance": "FIN",
        "accessibility": "ACC",
    }[dataset]


def _dimension_code(dimension: str) -> str:
    return {
        "completeness": "CMP",
        "validity": "VAL",
        "consistency": "CON",
        "uniqueness": "UNI",
        "timeliness": "TIM",
        "referential_integrity": "REF",
        "reconciliation": "REC",
    }[dimension]


def _fields(dataset: str, dimension: str) -> tuple[str, ...]:
    identifier = {
        "buildings": "building_id",
        "rooms": "room_id",
        "services": "service_id",
        "bookings": "booking_id",
        "clinical_activity": "activity_id",
        "workforce": "workforce_record_id",
        "finance": "finance_record_id",
        "accessibility": "accessibility_record_id",
    }[dataset]
    if dimension == "completeness":
        return (identifier,)
    if dimension == "referential_integrity":
        return ("parent_reference",)
    return (identifier, dimension)
