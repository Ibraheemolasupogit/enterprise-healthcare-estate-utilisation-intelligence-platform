"""Generation metadata helpers."""

from __future__ import annotations

from typing import Any


def build_metadata(
    *,
    config: Any,
    project_version: str,
    record_counts: dict[str, int],
    column_order: dict[str, list[str]],
    file_checksums: dict[str, str],
    quality_issue_count: int,
) -> dict[str, Any]:
    """Build deterministic metadata for generated synthetic data."""

    return {
        "column_order": column_order,
        "dataset_names": sorted(record_counts),
        "file_checksums": dict(sorted(file_checksums.items())),
        "generation_parameters": {
            "booking_count": config.booking_count,
            "building_count": config.building_count,
            "end_date": config.end_date.isoformat(),
            "financial_years": list(config.financial_years),
            "quality_issues_enabled": config.quality_issues_enabled,
            "room_count": config.room_count,
            "sample_data_scale": config.sample_data_scale,
            "service_count": config.service_count,
            "site_count": config.site_count,
            "start_date": config.start_date.isoformat(),
            "workforce_grain": config.workforce_grain,
        },
        "generator_version": "milestone-2.0",
        "intentional_quality_issue_count": quality_issue_count,
        "master_seed": config.master_seed,
        "project_version": project_version,
        "record_counts": dict(sorted(record_counts.items())),
        "reference_date": config.reference_date.isoformat(),
        "synthetic_data_notice": (
            "Synthetic source data for Northstar Community Health Partnership. "
            "No real patient, employee, organisation, estate or finance data is included."
        ),
    }
