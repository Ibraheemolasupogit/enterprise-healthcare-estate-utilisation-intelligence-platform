"""Focused Milestone 3 ingestion checks."""

from __future__ import annotations

from pathlib import Path

from estate_intelligence.ingestion.manifest import load_generation_metadata, verify_source_checksums


def verify_input_directory(input_dir: Path) -> dict[str, str]:
    """Verify a synthetic input directory before ingestion."""

    metadata = load_generation_metadata(input_dir)
    return verify_source_checksums(input_dir, metadata)
