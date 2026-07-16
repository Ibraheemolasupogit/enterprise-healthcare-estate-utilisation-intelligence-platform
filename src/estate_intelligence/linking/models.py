"""Entity-linking evidence models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LinkageResult:
    """Auditable entity-linkage result."""

    linkage_id: str
    entity_type: str
    source_dataset: str
    source_record_identifier: str
    source_value: str
    canonical_entity_id: str | None
    match_method: str
    match_score: float
    match_status: str
    parent_context: str
    normalised_value: str
    reason: str
    ingestion_run_id: str
