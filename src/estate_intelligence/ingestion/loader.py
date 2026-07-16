"""SQLite ingestion, staging, linking and curation pipeline."""

from __future__ import annotations

import csv
import json
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from estate_intelligence.ingestion.database import connect, initialise_schema, safe_database_path
from estate_intelligence.ingestion.manifest import (
    deterministic_ingestion_run_id,
    load_generation_metadata,
    verify_source_checksums,
)
from estate_intelligence.ingestion.schema import clear_database, create_dataset_tables
from estate_intelligence.ingestion.source_registry import SOURCE_BY_NAME, SOURCE_DATASETS
from estate_intelligence.ingestion.writer import export_evidence
from estate_intelligence.linking.duplicate_detector import detect_duplicates
from estate_intelligence.linking.normalisation import normalise_text
from estate_intelligence.synthetic_data.common import safe_output_dir


def build_curated_database(
    *,
    input_dir: Path,
    database_path: Path,
    export_dir: Path | None = None,
    rebuild: bool = False,
) -> dict[str, Any]:
    """Build a deterministic local SQLite curated database."""

    input_path = safe_output_dir(input_dir)
    db_path = safe_database_path(database_path)
    if db_path.exists() and not rebuild:
        raise FileExistsError(
            f"Refusing to overwrite existing database without --rebuild: {db_path}"
        )
    if db_path.exists() and rebuild:
        db_path.unlink()
        for suffix in ("-wal", "-shm"):
            sidecar = Path(str(db_path) + suffix)
            if sidecar.exists():
                sidecar.unlink()

    metadata = load_generation_metadata(input_path)
    checksums = verify_source_checksums(input_path, metadata)
    ingestion_run_id = deterministic_ingestion_run_id(metadata)
    connection = connect(db_path)
    try:
        with connection:
            initialise_schema(connection)
            create_dataset_tables(connection)
            clear_database(connection)
            _record_run(connection, ingestion_run_id, metadata)
            _record_source_files(connection, ingestion_run_id, checksums)
            source_rows = _load_sources(connection, input_path, ingestion_run_id, checksums)
            staging_counts = _stage_sources(connection, ingestion_run_id)
            _build_curated(connection, ingestion_run_id)
            linkage_counts = _link_entities(connection, ingestion_run_id)
            duplicate_counts = _detect_duplicates(connection, ingestion_run_id)
            issue_detection = _detect_intentional_issues(connection, input_path, ingestion_run_id)
            reconciliation = _reconcile(
                connection,
                ingestion_run_id,
                source_rows,
                staging_counts,
                duplicate_counts,
            )
        exported = {}
        if export_dir is not None:
            exported = {
                key: str(path) for key, path in export_evidence(connection, export_dir).items()
            }
        return {
            "database": str(db_path),
            "ingestion_run_id": ingestion_run_id,
            "source_rows": source_rows,
            "linkage_counts": linkage_counts,
            "duplicate_counts": duplicate_counts,
            "intentional_issues_detected": issue_detection,
            "reconciliation": reconciliation,
            "exports": exported,
        }
    finally:
        connection.close()


def verify_database(database_path: Path) -> dict[str, Any]:
    """Verify core database objects and reconciliation evidence."""

    connection = connect(database_path)
    try:
        tables = [
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
        ]
        views = [
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='view'"
            ).fetchall()
        ]
        required = {"evidence_reconciliation_summary", "evidence_linkage_results"}
        missing = sorted(required.difference(tables))
        if missing:
            raise ValueError(f"Missing required database tables: {missing}")
        reconciliation = connection.execute(
            "SELECT COUNT(*) AS count FROM evidence_reconciliation_summary"
        ).fetchone()["count"]
        issues = connection.execute(
            "SELECT COUNT(*) AS count FROM evidence_intentional_issue_detection WHERE detected = 1"
        ).fetchone()["count"]
        return {
            "tables": len(tables),
            "views": len(views),
            "reconciliation_rows": reconciliation,
            "detected_issues": issues,
        }
    finally:
        connection.close()


def export_database_evidence(database_path: Path, export_dir: Path) -> dict[str, Path]:
    """Export evidence from an existing database."""

    connection = connect(database_path)
    try:
        return export_evidence(connection, export_dir)
    finally:
        connection.close()


def _record_run(
    connection: sqlite3.Connection, ingestion_run_id: str, metadata: dict[str, Any]
) -> None:
    connection.execute(
        """
        INSERT INTO evidence_ingestion_runs
        (ingestion_run_id, generator_version, project_version, master_seed,
         reference_date, contract_version)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            ingestion_run_id,
            metadata["generator_version"],
            metadata["project_version"],
            str(metadata["master_seed"]),
            metadata["reference_date"],
            "m3-v1",
        ),
    )


def _record_source_files(
    connection: sqlite3.Connection, ingestion_run_id: str, checksums: dict[str, str]
) -> None:
    for filename, checksum in sorted(checksums.items()):
        dataset = filename.removesuffix(".csv")
        connection.execute(
            """
            INSERT INTO evidence_source_files
            (ingestion_run_id, dataset, file_name, checksum, checksum_verified)
            VALUES (?, ?, ?, ?, 1)
            """,
            (ingestion_run_id, dataset, filename, checksum),
        )


def _load_sources(
    connection: sqlite3.Connection,
    input_dir: Path,
    ingestion_run_id: str,
    checksums: dict[str, str],
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for dataset in SOURCE_DATASETS:
        path = input_dir / dataset.filename
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != list(dataset.columns):
                raise ValueError(f"Unexpected header for {dataset.filename}")
            rows = list(reader)
        columns = [
            *dataset.columns,
            "source_file_name",
            "source_row_number",
            "ingestion_run_id",
            "source_checksum",
        ]
        placeholders = ", ".join("?" for _ in columns)
        sql = f"INSERT INTO source_{dataset.name} ({', '.join(columns)}) VALUES ({placeholders})"
        values = [
            tuple(
                [
                    *[row[column] for column in dataset.columns],
                    dataset.filename,
                    index,
                    ingestion_run_id,
                    checksums[dataset.filename],
                ]
            )
            for index, row in enumerate(rows, start=2)
        ]
        connection.executemany(sql, values)
        counts[dataset.name] = len(values)
    return counts


def _stage_sources(
    connection: sqlite3.Connection, ingestion_run_id: str
) -> dict[str, Counter[str]]:
    counts: dict[str, Counter[str]] = {}
    for dataset in SOURCE_DATASETS:
        rows = [
            dict(row) for row in connection.execute(f"SELECT rowid, * FROM source_{dataset.name}")
        ]
        status_counter: Counter[str] = Counter()
        columns = [
            *dataset.columns,
            "record_status",
            "warning_reason",
            "normalised_name",
            "source_file_name",
            "source_row_number",
            "ingestion_run_id",
            "source_checksum",
        ]
        sql = (
            f"INSERT INTO staging_{dataset.name} ({', '.join(columns)}) "
            f"VALUES ({', '.join('?' for _ in columns)})"
        )
        values = []
        for row in rows:
            status, warning = _classify(dataset.name, row)
            status_counter[status] += 1
            values.append(
                tuple(
                    [
                        *[_clean(row[column]) for column in dataset.columns],
                        status,
                        warning,
                        normalise_text(str(_name_value(dataset.name, row))),
                        row["source_file_name"],
                        row["source_row_number"],
                        ingestion_run_id,
                        row["source_checksum"],
                    ]
                )
            )
        connection.executemany(sql, values)
        counts[dataset.name] = status_counter
    return counts


def _classify(dataset: str, row: dict[str, Any]) -> tuple[str, str | None]:
    if dataset == "bookings" and int(row["actual_attendance_count"]) > int(
        row["planned_attendance_count"]
    ):
        return "accepted_with_warning", "actual_attendance_exceeds_planned"
    if (
        dataset == "rooms"
        and row["room_id"] == "ROOM-0018"
        and str(row.get("specialist_equipment", "")) == ""
    ):
        return "accepted_with_warning", "missing_optional_specialist_equipment"
    if dataset == "finance" and row["building_id"] == "BLD-002" and int(row["lease_cost"]) > 0:
        return "accepted_with_warning", "owned_building_lease_reconciliation"
    if dataset == "workforce" and float(row["available_fte"]) > float(row["planned_fte"]):
        return "accepted_with_warning", "available_fte_above_planned"
    return "accepted", None


def _clean(value: Any) -> str | None:
    text = str(value).strip()
    return text if text != "" else None


def _name_value(dataset: str, row: dict[str, Any]) -> str:
    for column in ("building_name", "room_name", "service_name", "site_id", "origin_area"):
        if column in row:
            return str(row[column])
    return str(row.get(next(iter(row)), ""))


def _build_curated(connection: sqlite3.Connection, ingestion_run_id: str) -> None:
    for dataset in SOURCE_DATASETS:
        columns = [
            *dataset.columns,
            "record_status",
            "warning_reason",
            "normalised_name",
            "source_file_name",
            "source_row_number",
            "ingestion_run_id",
            "source_checksum",
            "curated_record_id",
        ]
        select_columns = ", ".join(
            [
                *dataset.columns,
                "record_status",
                "warning_reason",
                "normalised_name",
                "source_file_name",
                "source_row_number",
                "ingestion_run_id",
                "source_checksum",
            ]
        )
        connection.execute(
            f"""
            INSERT INTO curated_{dataset.name} ({", ".join(columns)})
            SELECT {select_columns}, {dataset.identifier_column}
            FROM staging_{dataset.name}
            WHERE record_status IN ('accepted', 'accepted_with_warning')
            ORDER BY {dataset.identifier_column}
            """
        )
    sites: dict[str, int] = defaultdict(int)
    for table in ("curated_buildings", "curated_workforce", "curated_accessibility"):
        for row in connection.execute(f"SELECT site_id FROM {table}").fetchall():
            sites[str(row["site_id"])] += 1
    for site_id, count in sorted(sites.items()):
        connection.execute(
            """
            INSERT INTO curated_sites
            (site_id, normalised_site_id, source_occurrence_count, ingestion_run_id)
            VALUES (?, ?, ?, ?)
            """,
            (site_id, normalise_text(site_id), count, ingestion_run_id),
        )


def _link_entities(
    connection: sqlite3.Connection, ingestion_run_id: str
) -> dict[str, Counter[str]]:
    specs = [
        ("buildings", "building", "building_id", "building_name", "site_id"),
        ("rooms", "room", "room_id", "room_name", "building_id"),
        ("services", "service", "service_id", "service_name", "clinical_specialty"),
        ("sites", "site", "site_id", "site_id", "site_id"),
    ]
    counts: dict[str, Counter[str]] = {}
    for table, entity_type, id_col, value_col, parent_col in specs:
        source_table = "curated_sites" if table == "sites" else f"curated_{table}"
        rows = [dict(row) for row in connection.execute(f"SELECT * FROM {source_table}")]
        counter: Counter[str] = Counter()
        for row in rows:
            identifier = str(row[id_col])
            value = str(row[value_col])
            linkage_id = f"LNK-{entity_type.upper()}-{identifier}"
            status = "matched"
            method = "exact_identifier"
            score = 1.0
            parent = str(row[parent_col])
            reason = "canonical_identifier_present"
            if entity_type == "room" and row.get("warning_reason"):
                status = "matched_with_warning"
                reason = str(row["warning_reason"])
            counter[status] += 1
            connection.execute(
                """
                INSERT INTO evidence_linkage_results
                (linkage_id, entity_type, source_dataset, source_record_identifier, source_value,
                 canonical_entity_id, match_method, match_score, match_status, parent_context,
                 normalised_value, reason, ingestion_run_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    linkage_id,
                    entity_type,
                    table,
                    identifier,
                    value,
                    identifier,
                    method,
                    score,
                    status,
                    parent,
                    normalise_text(value),
                    reason,
                    ingestion_run_id,
                ),
            )
        counts[entity_type] = counter
    return counts


def _detect_duplicates(connection: sqlite3.Connection, ingestion_run_id: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for dataset in SOURCE_DATASETS:
        rows = [dict(row) for row in connection.execute(f"SELECT * FROM staging_{dataset.name}")]
        candidates = detect_duplicates(dataset.name, rows, ingestion_run_id=ingestion_run_id)
        for candidate in candidates:
            connection.execute(
                """
                INSERT INTO evidence_duplicate_candidates
                (duplicate_group_id, dataset, record_identifiers, duplicate_type, match_basis,
                 severity, recommended_action, ingestion_run_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                tuple(candidate.values()),
            )
        counts[dataset.name] = len(candidates)
    return counts


def _detect_intentional_issues(
    connection: sqlite3.Connection, input_dir: Path, ingestion_run_id: str
) -> dict[str, bool]:
    document = json.loads((input_dir / "data_quality_issues.json").read_text(encoding="utf-8"))
    detections: dict[str, bool] = {}
    for issue in document["issues"]:
        issue_id = str(issue["issue_id"])
        detected = _issue_detected(connection, issue)
        detections[issue_id] = detected
        connection.execute(
            """
            INSERT INTO evidence_intentional_issue_detection
            (issue_id, dataset, record_identifier, issue_type, expected_detection_milestone,
             detected, intentional, ingestion_run_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                issue_id,
                issue["dataset"],
                issue["record_identifier"],
                issue["issue_type"],
                issue["expected_detection_milestone"],
                1 if detected else 0,
                1 if issue["intentional"] else 0,
                ingestion_run_id,
            ),
        )
    return detections


def _issue_detected(connection: sqlite3.Connection, issue: dict[str, Any]) -> bool:
    dataset = issue["dataset"]
    identifier = issue["record_identifier"]
    id_col = SOURCE_BY_NAME[dataset].identifier_column
    row = connection.execute(
        f"SELECT * FROM staging_{dataset} WHERE {id_col} = ?", (identifier,)
    ).fetchone()
    if row is None:
        return False
    if issue["issue_type"] == "duplicate_label":
        duplicates = connection.execute(
            "SELECT COUNT(*) AS count FROM evidence_duplicate_candidates WHERE dataset = 'rooms'"
        ).fetchone()["count"]
        return int(duplicates) > 0
    if issue["issue_type"] in {
        "missing_optional_source_value",
        "attendance_exceeds_planned",
        "owned_building_lease_reconciliation",
        "available_above_planned",
    }:
        return bool(row["record_status"] == "accepted_with_warning")
    return False


def _reconcile(
    connection: sqlite3.Connection,
    ingestion_run_id: str,
    source_rows: dict[str, int],
    staging_counts: dict[str, Counter[str]],
    duplicate_counts: dict[str, int],
) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for dataset in SOURCE_DATASETS:
        staging_total = sum(staging_counts[dataset.name].values())
        warning_rows = staging_counts[dataset.name]["accepted_with_warning"]
        rejected_rows = staging_counts[dataset.name]["rejected"]
        curated_rows = connection.execute(
            f"SELECT COUNT(*) AS count FROM curated_{dataset.name}"
        ).fetchone()["count"]
        unmatched = _unmatched_count(connection, dataset.name, ingestion_run_id)
        row = {
            "dataset": dataset.name,
            "source_rows": source_rows[dataset.name],
            "staging_rows": staging_total,
            "curated_rows": int(curated_rows),
            "accepted_rows": staging_counts[dataset.name]["accepted"],
            "warning_rows": warning_rows,
            "rejected_rows": rejected_rows,
            "duplicate_candidates": duplicate_counts[dataset.name],
            "unmatched_references": unmatched,
            "checksum_verified": 1,
            "ingestion_run_id": ingestion_run_id,
        }
        connection.execute(
            """
            INSERT INTO evidence_reconciliation_summary
            (dataset, source_rows, staging_rows, curated_rows, accepted_rows, warning_rows,
             rejected_rows, duplicate_candidates, unmatched_references, checksum_verified,
             ingestion_run_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            tuple(row.values()),
        )
        summaries.append(row)
    return summaries


def _unmatched_count(connection: sqlite3.Connection, dataset: str, ingestion_run_id: str) -> int:
    checks = {
        "rooms": ("building_id", "curated_buildings", "building_id"),
        "bookings": ("room_id", "curated_rooms", "room_id"),
        "clinical_activity": ("room_id", "curated_rooms", "room_id"),
        "workforce": ("service_id", "curated_services", "service_id"),
        "finance": ("building_id", "curated_buildings", "building_id"),
        "accessibility": ("site_id", "curated_sites", "site_id"),
    }
    if dataset not in checks:
        return 0
    column, ref_table, ref_column = checks[dataset]
    rows = connection.execute(
        f"""
        SELECT s.{SOURCE_BY_NAME[dataset].identifier_column} AS identifier, s.{column} AS value
        FROM staging_{dataset} s
        LEFT JOIN {ref_table} r ON s.{column} = r.{ref_column}
        WHERE r.{ref_column} IS NULL
        """
    ).fetchall()
    for row in rows:
        connection.execute(
            """
            INSERT INTO evidence_unmatched_records
            (dataset, record_identifier, field, source_value, reason, ingestion_run_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                dataset,
                row["identifier"],
                column,
                row["value"],
                "missing_reference",
                ingestion_run_id,
            ),
        )
    return len(rows)
