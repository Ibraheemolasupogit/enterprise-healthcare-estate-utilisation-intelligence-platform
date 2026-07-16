"""Source manifest and checksum verification."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from estate_intelligence.synthetic_data.common import sha256_file


def load_generation_metadata(input_dir: Path) -> dict[str, Any]:
    """Load Milestone 2 generation metadata."""

    metadata_path = input_dir / "generation_metadata.json"
    if not metadata_path.exists():
        raise FileNotFoundError(f"Missing generation metadata: {metadata_path}")
    document = json.loads(metadata_path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise ValueError("generation metadata must be a JSON object")
    return document


def verify_source_checksums(input_dir: Path, metadata: dict[str, Any]) -> dict[str, str]:
    """Verify all source file checksums and return them."""

    checksums = metadata["file_checksums"]
    verified: dict[str, str] = {}
    for filename, expected in checksums.items():
        if not filename.endswith(".csv"):
            continue
        actual = sha256_file(input_dir / filename)
        if actual != expected:
            raise ValueError(f"Checksum mismatch for {filename}")
        verified[filename] = actual
    return verified


def deterministic_ingestion_run_id(
    metadata: dict[str, Any], contract_version: str = "m3-v1"
) -> str:
    """Create a deterministic ingestion-run identifier from stable metadata."""

    payload = {
        "contract_version": contract_version,
        "generator_version": metadata["generator_version"],
        "master_seed": metadata["master_seed"],
        "reference_date": metadata["reference_date"],
        "file_checksums": metadata["file_checksums"],
    }
    import hashlib

    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return f"ING-{digest[:16]}"
