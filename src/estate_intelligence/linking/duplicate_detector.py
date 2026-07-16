"""Deterministic duplicate detection for Milestone 3 evidence."""

from __future__ import annotations

import hashlib
from collections import defaultdict
from collections.abc import Iterable, Mapping
from typing import Any

from estate_intelligence.linking.normalisation import normalise_text


def duplicate_group_id(dataset: str, duplicate_type: str, basis: str) -> str:
    """Create a stable duplicate-group identifier."""

    digest = hashlib.sha256(f"{dataset}|{duplicate_type}|{basis}".encode()).hexdigest()
    return f"DUP-{digest[:12]}"


def detect_duplicates(
    dataset: str,
    rows: Iterable[Mapping[str, Any]],
    *,
    ingestion_run_id: str,
) -> list[dict[str, Any]]:
    """Detect a focused set of duplicate candidates."""

    candidates: list[dict[str, Any]] = []
    rows_list = list(rows)
    id_column = (
        next(column for column in rows_list[0] if column.endswith("_id")) if rows_list else ""
    )
    by_id: dict[str, list[str]] = defaultdict(list)
    for row in rows_list:
        by_id[str(row.get(id_column, ""))].append(str(row.get(id_column, "")))
    for identifier, identifiers in sorted(by_id.items()):
        if identifier and len(identifiers) > 1:
            candidates.append(
                _candidate(
                    dataset,
                    identifiers,
                    "duplicate_identifier",
                    identifier,
                    "high",
                    ingestion_run_id,
                )
            )

    if dataset == "rooms":
        by_room_name: dict[str, list[str]] = defaultdict(list)
        by_global_room_name: dict[str, list[str]] = defaultdict(list)
        for row in rows_list:
            basis = f"{row['building_id']}|{normalise_text(str(row['room_name']))}"
            by_room_name[basis].append(str(row["room_id"]))
            by_global_room_name[normalise_text(str(row["room_name"]))].append(str(row["room_id"]))
        for basis, identifiers in sorted(by_room_name.items()):
            if len(identifiers) > 1:
                candidates.append(
                    _candidate(
                        dataset,
                        identifiers,
                        "duplicate_room_name_within_building",
                        basis,
                        "low",
                        ingestion_run_id,
                    )
                )
        for basis, identifiers in sorted(by_global_room_name.items()):
            if len(identifiers) > 1:
                candidates.append(
                    _candidate(
                        dataset,
                        identifiers,
                        "duplicate_room_name_global",
                        basis,
                        "low",
                        ingestion_run_id,
                    )
                )

    if dataset == "services":
        by_name: dict[str, list[str]] = defaultdict(list)
        for row in rows_list:
            by_name[normalise_text(str(row["service_name"]))].append(str(row["service_id"]))
        for basis, identifiers in sorted(by_name.items()):
            if len(identifiers) > 1:
                candidates.append(
                    _candidate(
                        dataset,
                        identifiers,
                        "duplicate_service_name",
                        basis,
                        "medium",
                        ingestion_run_id,
                    )
                )
    return candidates


def _candidate(
    dataset: str,
    identifiers: list[str],
    duplicate_type: str,
    basis: str,
    severity: str,
    ingestion_run_id: str,
) -> dict[str, Any]:
    return {
        "duplicate_group_id": duplicate_group_id(dataset, duplicate_type, basis),
        "dataset": dataset,
        "record_identifiers": ",".join(sorted(identifiers)),
        "duplicate_type": duplicate_type,
        "match_basis": basis,
        "severity": severity,
        "recommended_action": "review_source_records",
        "ingestion_run_id": ingestion_run_id,
    }
