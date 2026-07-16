"""Typed ingestion models and summaries."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DatabaseConfig:
    """Runtime database configuration."""

    path: Path
    batch_size: int = 500
    source_prefix: str = "source"
    staging_prefix: str = "staging"
    curated_prefix: str = "curated"
    evidence_prefix: str = "evidence"


@dataclass(frozen=True)
class DatasetReconciliation:
    """Reconciliation counts for one source dataset."""

    dataset: str
    source_rows: int
    staging_rows: int
    curated_rows: int
    accepted_rows: int
    warning_rows: int
    rejected_rows: int
    duplicate_candidates: int
    unmatched_references: int
    checksum_verified: bool
