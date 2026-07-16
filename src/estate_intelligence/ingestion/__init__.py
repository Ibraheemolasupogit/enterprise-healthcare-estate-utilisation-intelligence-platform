"""Local SQLite ingestion pipeline for Milestone 3."""

from estate_intelligence.ingestion.loader import (
    build_curated_database,
    export_database_evidence,
    verify_database,
)

__all__ = ["build_curated_database", "export_database_evidence", "verify_database"]
