"""Communication provenance helpers."""

from __future__ import annotations

from pathlib import Path

from estate_intelligence.reporting.rendering import file_checksum


def build_provenance_rows(communication_run_id: str, output_dir: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for index, path in enumerate(sorted(output_dir.iterdir()), start=1):
        if path.is_file():
            rows.append(
                {
                    "provenance_id": f"PROV-{index:03d}",
                    "communication_run_id": communication_run_id,
                    "artefact_name": path.name,
                    "source_type": "generated_output",
                    "source_reference": f"outputs/communication/{path.name}",
                    "checksum": file_checksum(path),
                }
            )
    return rows
