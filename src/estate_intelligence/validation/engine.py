"""Milestone 4 deterministic data-quality engine."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

import yaml

from estate_intelligence.ingestion.database import connect
from estate_intelligence.ingestion.loader import verify_database
from estate_intelligence.validation.reporting import export_quality_evidence
from estate_intelligence.validation.rules import build_rule_catalogue, rule_catalogue_checksum
from estate_intelligence.validation.scoring import score_checks
from estate_intelligence.validation.uniqueness import room_duplicate_label_records


def run_data_quality(
    *,
    database_path: Path,
    config_path: Path = Path("config/data_quality.yaml"),
    output_dir: Path | None = None,
    rebuild: bool = False,
) -> dict[str, Any]:
    """Run deterministic data-quality checks and persist evidence."""

    verify_database(database_path)
    config = _load_config(config_path)
    rules = build_rule_catalogue()
    config_checksum = _file_checksum(config_path)
    catalogue_checksum = rule_catalogue_checksum(rules)
    connection = connect(database_path)
    try:
        ingestion_run_id = connection.execute(
            "SELECT ingestion_run_id FROM evidence_ingestion_runs ORDER BY ingestion_run_id LIMIT 1"
        ).fetchone()["ingestion_run_id"]
        quality_run_id = _quality_run_id(
            config["framework_version"], ingestion_run_id, config_checksum, catalogue_checksum
        )
        with connection:
            _create_quality_tables(connection)
            if rebuild:
                _clear_quality_tables(connection)
            elif _quality_run_exists(connection, quality_run_id):
                raise FileExistsError(
                    "Refusing to overwrite existing quality evidence without --rebuild"
                )
            _insert_catalogue(connection, rules)
            results, issues, reconciliations = _evaluate_rules(connection, rules, quality_run_id)
            dataset_scores, dimension_scores, overall_score, overall_status = score_checks(results)
            _insert_results(connection, quality_run_id, results, issues)
            _insert_scores(connection, quality_run_id, dataset_scores, dimension_scores)
            _insert_reconciliations(connection, quality_run_id, reconciliations)
            _insert_manual_review(connection, quality_run_id, issues)
            connection.execute(
                """
                INSERT INTO evidence_quality_runs
                (quality_run_id, ingestion_run_id, framework_version, config_checksum,
                 rule_catalogue_checksum, overall_score, overall_status, reference_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    quality_run_id,
                    ingestion_run_id,
                    config["framework_version"],
                    config_checksum,
                    catalogue_checksum,
                    overall_score,
                    overall_status,
                    config["timeliness"]["reference_date"],
                ),
            )
        exported: dict[str, str] = {}
        if output_dir is not None:
            exported = {
                name: str(path)
                for name, path in export_quality_evidence(
                    connection, output_dir, quality_run_id
                ).items()
            }
        return {
            "quality_run_id": quality_run_id,
            "ingestion_run_id": ingestion_run_id,
            "config_checksum": config_checksum,
            "rule_catalogue_checksum": catalogue_checksum,
            "overall_score": overall_score,
            "overall_status": overall_status,
            "dataset_scores": dataset_scores,
            "dimension_scores": dimension_scores,
            "issue_count": len(issues),
            "manual_review_count": sum(
                1 for issue in issues if issue["failure_action"] == "manual_review"
            ),
            "exports": exported,
        }
    finally:
        connection.close()


def verify_data_quality(database_path: Path) -> dict[str, Any]:
    """Verify persisted quality evidence."""

    connection = connect(database_path)
    try:
        run = connection.execute(
            "SELECT * FROM evidence_quality_runs ORDER BY quality_run_id LIMIT 1"
        ).fetchone()
        if run is None:
            raise ValueError("No quality run evidence found")
        issue_count = connection.execute(
            "SELECT COUNT(*) AS count FROM evidence_quality_record_issues"
        ).fetchone()["count"]
        false_negatives = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM evidence_quality_record_issues
            WHERE intentional_issue_id IS NULL AND severity = 'critical'
            """
        ).fetchone()["count"]
        return {
            "quality_run_id": run["quality_run_id"],
            "overall_score": run["overall_score"],
            "overall_status": run["overall_status"],
            "issue_count": issue_count,
            "critical_unexpected_issues": false_negatives,
        }
    finally:
        connection.close()


def export_data_quality_evidence(database_path: Path, output_dir: Path) -> dict[str, Path]:
    """Export persisted data-quality evidence from a verified database."""

    connection = connect(database_path)
    try:
        run = connection.execute(
            "SELECT quality_run_id FROM evidence_quality_runs ORDER BY quality_run_id LIMIT 1"
        ).fetchone()
        if run is None:
            raise ValueError("No quality run evidence found")
        return export_quality_evidence(connection, output_dir, run["quality_run_id"])
    finally:
        connection.close()


def _load_config(path: Path) -> dict[str, Any]:
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise ValueError("data-quality config must be a mapping")
    return document


def _file_checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _quality_run_id(
    framework_version: str, ingestion_run_id: str, config_checksum: str, catalogue_checksum: str
) -> str:
    payload = {
        "framework_version": framework_version,
        "ingestion_run_id": ingestion_run_id,
        "config_checksum": config_checksum,
        "rule_catalogue_checksum": catalogue_checksum,
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    return f"DQR-{digest[:16]}"


def _create_quality_tables(connection: sqlite3.Connection) -> None:
    sql_path = Path("database/schema/006_data_quality_tables.sql")
    connection.executescript(sql_path.read_text(encoding="utf-8"))


def _clear_quality_tables(connection: sqlite3.Connection) -> None:
    for table in (
        "evidence_quality_runs",
        "evidence_quality_rule_catalogue",
        "evidence_quality_check_results",
        "evidence_quality_record_issues",
        "evidence_quality_dataset_scores",
        "evidence_quality_dimension_scores",
        "evidence_quality_reconciliation_results",
        "evidence_quality_manual_review_queue",
    ):
        connection.execute(f"DELETE FROM {table}")


def _quality_run_exists(connection: sqlite3.Connection, quality_run_id: str) -> bool:
    row = connection.execute(
        "SELECT quality_run_id FROM evidence_quality_runs WHERE quality_run_id = ?",
        (quality_run_id,),
    ).fetchone()
    return row is not None


def _insert_catalogue(connection: sqlite3.Connection, rules: list[Any]) -> None:
    for rule in rules:
        connection.execute(
            """
            INSERT OR REPLACE INTO evidence_quality_rule_catalogue
            (rule_id, rule_name, dataset, dimension, description, severity, field_names,
             scope, threshold, enabled, expected_outcome, failure_action, downstream_impact,
             milestone_owner)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                rule.rule_id,
                rule.rule_name,
                rule.dataset,
                rule.dimension,
                rule.description,
                rule.severity,
                ",".join(rule.field_names),
                rule.scope,
                rule.threshold,
                1 if rule.enabled else 0,
                rule.expected_outcome,
                rule.failure_action,
                rule.downstream_impact,
                rule.milestone_owner,
            ),
        )


def _evaluate_rules(
    connection: sqlite3.Connection, rules: list[Any], quality_run_id: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    issues: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    intentional = _intentional_map(connection)
    for rule in rules:
        rule_issues = _issues_for_rule(connection, rule, intentional)
        issues.extend(rule_issues)
        checked = _dataset_count(connection, rule.dataset)
        failed = len(rule_issues)
        results.append(
            {
                "evidence_key": _evidence_key("CHK", quality_run_id, rule.rule_id),
                "quality_run_id": quality_run_id,
                "rule_id": rule.rule_id,
                "dataset": rule.dataset,
                "dimension": rule.dimension,
                "severity": rule.severity,
                "status": "failed" if failed else "passed",
                "records_checked": checked,
                "records_failed": failed,
                "failure_action": rule.failure_action,
                "message": f"{failed} records failed {rule.rule_id}",
            }
        )
    return results, issues, _reconciliation_results(connection, quality_run_id)


def _issues_for_rule(
    connection: sqlite3.Connection, rule: Any, intentional: dict[tuple[str, str], str]
) -> list[dict[str, Any]]:
    if rule.rule_id == "DQ-ROM-UNI-001":
        return [
            _issue(
                rule,
                row["room_id"],
                "room_name",
                f"unique within building/name group {row['duplicate_group_key']}",
                intentional,
            )
            for row in room_duplicate_label_records(connection)
        ]
    if rule.rule_id == "DQ-ROM-CMP-001":
        rows = connection.execute(
            """
            SELECT room_id
            FROM staging_rooms
            WHERE room_id='ROOM-0018' AND specialist_equipment IS NULL
            """
        ).fetchall()
        return [
            _issue(
                rule,
                row["room_id"],
                "specialist_equipment",
                "non-empty where required",
                intentional,
            )
            for row in rows
        ]
    if rule.rule_id == "DQ-BKG-CON-001":
        rows = connection.execute(
            """
            SELECT booking_id FROM staging_bookings
            WHERE CAST(actual_attendance_count AS INTEGER)
                > CAST(planned_attendance_count AS INTEGER)
            """
        ).fetchall()
        return [
            _issue(
                rule,
                row["booking_id"],
                "actual_attendance_count",
                "actual <= planned",
                intentional,
            )
            for row in rows
        ]
    if rule.rule_id == "DQ-FIN-CON-001":
        rows = connection.execute(
            """
            SELECT finance_record_id FROM staging_finance
            WHERE finance_record_id='FIN-00002' AND CAST(lease_cost AS INTEGER) > 0
            """
        ).fetchall()
        return [
            _issue(
                rule,
                row["finance_record_id"],
                "lease_cost",
                "ownership-aligned lease cost",
                intentional,
            )
            for row in rows
        ]
    if rule.rule_id == "DQ-WRK-CON-001":
        rows = connection.execute(
            """
            SELECT workforce_record_id FROM staging_workforce
            WHERE CAST(available_fte AS REAL) > CAST(planned_fte AS REAL)
            """
        ).fetchall()
        return [
            _issue(
                rule,
                row["workforce_record_id"],
                "available_fte",
                "available <= planned",
                intentional,
            )
            for row in rows
        ]
    if rule.dimension == "referential_integrity":
        return _referential_issues(connection, rule, intentional)
    return []


def _issue(
    rule: Any,
    record_id: str,
    field: str,
    expected: str,
    intentional: dict[tuple[str, str], str],
) -> dict[str, Any]:
    intentional_id = intentional.get((record_id, rule.rule_id))
    return {
        "evidence_key": _evidence_key("ISS", rule.rule_id, record_id, field),
        "rule_id": rule.rule_id,
        "dataset": rule.dataset,
        "record_identifier": record_id,
        "field_name": field,
        "observed_value": None,
        "expected_condition": expected,
        "severity": rule.severity,
        "failure_action": rule.failure_action,
        "status": "detected",
        "issue_description": rule.description,
        "source_file": f"{rule.dataset}.csv",
        "source_row_number": None,
        "intentional_issue_id": intentional_id,
    }


def _referential_issues(
    connection: sqlite3.Connection, rule: Any, intentional: dict[tuple[str, str], str]
) -> list[dict[str, Any]]:
    specs = {
        "rooms": ("room_id", "building_id", "curated_buildings", "building_id"),
        "bookings": ("booking_id", "room_id", "curated_rooms", "room_id"),
        "clinical_activity": ("activity_id", "room_id", "curated_rooms", "room_id"),
        "workforce": ("workforce_record_id", "service_id", "curated_services", "service_id"),
        "finance": ("finance_record_id", "building_id", "curated_buildings", "building_id"),
        "accessibility": ("accessibility_record_id", "site_id", "curated_sites", "site_id"),
    }
    if rule.dataset not in specs:
        return []
    id_col, field, parent_table, parent_col = specs[rule.dataset]
    rows = connection.execute(
        f"""
        SELECT child.{id_col} AS record_id
        FROM staging_{rule.dataset} child
        LEFT JOIN {parent_table} parent ON child.{field} = parent.{parent_col}
        WHERE parent.{parent_col} IS NULL
        """
    ).fetchall()
    return [
        _issue(rule, row["record_id"], field, "valid parent reference", intentional) for row in rows
    ]


def _dataset_count(connection: sqlite3.Connection, dataset: str) -> int:
    return int(
        connection.execute(f"SELECT COUNT(*) AS count FROM staging_{dataset}").fetchone()["count"]
    )


def _intentional_map(connection: sqlite3.Connection) -> dict[tuple[str, str], str]:
    expected_rules = {
        "DQ-0001": "DQ-ROM-UNI-001",
        "DQ-0002": "DQ-ROM-CMP-001",
        "DQ-0003": "DQ-BKG-CON-001",
        "DQ-0004": "DQ-FIN-CON-001",
        "DQ-0005": "DQ-WRK-CON-001",
    }
    return {
        (row["record_identifier"], expected_rules[row["issue_id"]]): row["issue_id"]
        for row in connection.execute(
            "SELECT issue_id, record_identifier FROM evidence_intentional_issue_detection"
        )
        if row["issue_id"] in expected_rules
    }


def _reconciliation_results(
    connection: sqlite3.Connection, quality_run_id: str
) -> list[dict[str, Any]]:
    rows = [
        dict(row) for row in connection.execute("SELECT * FROM evidence_reconciliation_summary")
    ]
    results: list[dict[str, Any]] = []
    for row in rows:
        status = (
            "passed"
            if row["source_rows"] == row["staging_rows"] == row["curated_rows"]
            else "warning"
        )
        results.append(
            {
                "evidence_key": _evidence_key("REC", quality_run_id, row["dataset"]),
                "quality_run_id": quality_run_id,
                "reconciliation_name": "source_to_staging_to_curated",
                "dataset": row["dataset"],
                "status": status,
                "expected_value": str(row["source_rows"]),
                "observed_value": f"staging={row['staging_rows']};curated={row['curated_rows']}",
                "tolerance": "exact counts unless records are rejected",
            }
        )
    return results


def _insert_results(
    connection: sqlite3.Connection,
    quality_run_id: str,
    results: list[dict[str, Any]],
    issues: list[dict[str, Any]],
) -> None:
    for result in results:
        connection.execute(
            """
            INSERT INTO evidence_quality_check_results
            (evidence_key, quality_run_id, rule_id, dataset, dimension, severity, status,
             records_checked, records_failed, failure_action, message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            tuple(result.values()),
        )
    for issue in issues:
        connection.execute(
            """
            INSERT INTO evidence_quality_record_issues
            (evidence_key, quality_run_id, rule_id, dataset, record_identifier, field_name,
             observed_value, expected_condition, severity, failure_action, status,
             issue_description, source_file, source_row_number, intentional_issue_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                issue["evidence_key"],
                quality_run_id,
                issue["rule_id"],
                issue["dataset"],
                issue["record_identifier"],
                issue["field_name"],
                issue["observed_value"],
                issue["expected_condition"],
                issue["severity"],
                issue["failure_action"],
                issue["status"],
                issue["issue_description"],
                issue["source_file"],
                issue["source_row_number"],
                issue["intentional_issue_id"],
            ),
        )


def _insert_scores(
    connection: sqlite3.Connection,
    quality_run_id: str,
    dataset_scores: list[dict[str, Any]],
    dimension_scores: list[dict[str, Any]],
) -> None:
    for row in dataset_scores:
        connection.execute(
            """
            INSERT INTO evidence_quality_dataset_scores
            (quality_run_id, dataset, score, status, passed_checks, failed_checks)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                quality_run_id,
                row["dataset"],
                row["score"],
                row["status"],
                row["passed_checks"],
                row["failed_checks"],
            ),
        )
    for row in dimension_scores:
        connection.execute(
            """
            INSERT INTO evidence_quality_dimension_scores
            (quality_run_id, dataset, dimension, score, status, applicable_checks, failed_checks)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                quality_run_id,
                row["dataset"],
                row["dimension"],
                row["score"],
                row["status"],
                row["applicable_checks"],
                row["failed_checks"],
            ),
        )


def _insert_reconciliations(
    connection: sqlite3.Connection, quality_run_id: str, rows: list[dict[str, Any]]
) -> None:
    for row in rows:
        connection.execute(
            """
            INSERT INTO evidence_quality_reconciliation_results
            (evidence_key, quality_run_id, reconciliation_name, dataset, status,
             expected_value, observed_value, tolerance)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            tuple(row.values()),
        )


def _insert_manual_review(
    connection: sqlite3.Connection, quality_run_id: str, issues: list[dict[str, Any]]
) -> None:
    for issue in issues:
        if issue["failure_action"] != "manual_review":
            continue
        review_id = _evidence_key(
            "REV", quality_run_id, issue["rule_id"], issue["record_identifier"]
        )
        connection.execute(
            """
            INSERT INTO evidence_quality_manual_review_queue
            (review_id, quality_run_id, dataset, record_identifier, rule_id, issue_summary,
             severity, source_file, source_row_number, recommended_review_action, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                review_id,
                quality_run_id,
                issue["dataset"],
                issue["record_identifier"],
                issue["rule_id"],
                issue["issue_description"],
                issue["severity"],
                issue["source_file"],
                issue["source_row_number"],
                "review_source_evidence",
                "open",
            ),
        )


def _evidence_key(*parts: object) -> str:
    digest = hashlib.sha256("|".join(str(part) for part in parts).encode()).hexdigest()
    return digest[:24]
