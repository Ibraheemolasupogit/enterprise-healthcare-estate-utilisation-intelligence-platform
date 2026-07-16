import sqlite3
from pathlib import Path
from typing import Any

from estate_intelligence.ingestion.loader import build_curated_database
from estate_intelligence.validation.engine import run_data_quality
from estate_intelligence.validation.uniqueness import room_duplicate_label_records


def test_quality_evidence_tables_are_populated(tmp_path: Path) -> None:
    database = tmp_path / "estate.db"
    build_curated_database(input_dir=Path("data/sample"), database_path=database, rebuild=True)
    run_data_quality(database_path=database, rebuild=True)

    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    try:
        counts = {
            table: connection.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()["count"]
            for table in (
                "evidence_quality_runs",
                "evidence_quality_rule_catalogue",
                "evidence_quality_check_results",
                "evidence_quality_record_issues",
                "evidence_quality_dataset_scores",
                "evidence_quality_dimension_scores",
                "evidence_quality_reconciliation_results",
                "evidence_quality_manual_review_queue",
            )
        }
        defects = [
            row["intentional_issue_id"]
            for row in connection.execute(
                """
                SELECT DISTINCT intentional_issue_id
                FROM evidence_quality_record_issues
                WHERE intentional_issue_id IS NOT NULL
                ORDER BY intentional_issue_id
                """
            )
        ]
        room_duplicate_issues = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM evidence_quality_record_issues
            WHERE rule_id = 'DQ-ROM-UNI-001'
            """
        ).fetchone()["count"]
        manual_review_ids = [
            row["record_identifier"]
            for row in connection.execute(
                """
                SELECT record_identifier
                FROM evidence_quality_manual_review_queue
                ORDER BY dataset, record_identifier
                """
            )
        ]
    finally:
        connection.close()

    assert counts["evidence_quality_runs"] == 1
    assert counts["evidence_quality_rule_catalogue"] == 56
    assert counts["evidence_quality_check_results"] == 56
    assert counts["evidence_quality_dataset_scores"] == 8
    assert counts["evidence_quality_dimension_scores"] == 56
    assert counts["evidence_quality_reconciliation_results"] == 8
    assert counts["evidence_quality_record_issues"] == 6
    assert counts["evidence_quality_manual_review_queue"] == 4
    assert room_duplicate_issues == 2
    assert manual_review_ids == ["BOOK-000025", "FIN-00002", "ROOM-0002", "ROOM-0026"]
    assert defects == ["DQ-0001", "DQ-0002", "DQ-0003", "DQ-0004", "DQ-0005"]


def test_quality_room_duplicate_pair_flags_exact_members(tmp_path: Path) -> None:
    database = tmp_path / "estate.db"
    build_curated_database(input_dir=Path("data/sample"), database_path=database, rebuild=True)
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    try:
        source_rooms_before = _table_rows(connection, "source_rooms", "room_id")
        curated_rooms_before = _table_rows(connection, "curated_rooms", "room_id")
        duplicates = room_duplicate_label_records(connection)
    finally:
        connection.close()

    assert [row["room_id"] for row in duplicates] == ["ROOM-0002", "ROOM-0026"]
    assert {row["duplicate_group_key"] for row in duplicates} == {"BLD-002|treatment 8"}

    run_data_quality(database_path=database, rebuild=True)
    run_data_quality(database_path=database, rebuild=True)

    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    try:
        duplicate_issue_ids = [
            row["record_identifier"]
            for row in connection.execute(
                """
                SELECT record_identifier
                FROM evidence_quality_record_issues
                WHERE rule_id = 'DQ-ROM-UNI-001'
                ORDER BY record_identifier
                """
            )
        ]
        duplicate_result = connection.execute(
            """
            SELECT status, records_checked, records_failed
            FROM evidence_quality_check_results
            WHERE rule_id = 'DQ-ROM-UNI-001'
            """
        ).fetchone()
        manual_review_ids = [
            row["record_identifier"]
            for row in connection.execute(
                """
                SELECT record_identifier
                FROM evidence_quality_manual_review_queue
                WHERE rule_id = 'DQ-ROM-UNI-001'
                ORDER BY record_identifier
                """
            )
        ]
        defects = [
            row["intentional_issue_id"]
            for row in connection.execute(
                """
                SELECT DISTINCT intentional_issue_id
                FROM evidence_quality_record_issues
                WHERE intentional_issue_id IS NOT NULL
                ORDER BY intentional_issue_id
                """
            )
        ]
        counts = {
            table: connection.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()["count"]
            for table in (
                "evidence_quality_runs",
                "evidence_quality_record_issues",
                "evidence_quality_manual_review_queue",
            )
        }
        source_rooms_after = _table_rows(connection, "source_rooms", "room_id")
        curated_rooms_after = _table_rows(connection, "curated_rooms", "room_id")
    finally:
        connection.close()

    assert duplicate_issue_ids == ["ROOM-0002", "ROOM-0026"]
    assert dict(duplicate_result) == {
        "status": "failed",
        "records_checked": 56,
        "records_failed": 2,
    }
    assert manual_review_ids == ["ROOM-0002", "ROOM-0026"]
    assert counts == {
        "evidence_quality_runs": 1,
        "evidence_quality_record_issues": 6,
        "evidence_quality_manual_review_queue": 4,
    }
    assert defects == ["DQ-0001", "DQ-0002", "DQ-0003", "DQ-0004", "DQ-0005"]
    assert source_rooms_after == source_rooms_before
    assert curated_rooms_after == curated_rooms_before


def _table_rows(
    connection: sqlite3.Connection, table: str, order_column: str
) -> list[dict[str, Any]]:
    return [
        dict(row) for row in connection.execute(f"SELECT * FROM {table} ORDER BY {order_column}")
    ]
