import sqlite3

from estate_intelligence.validation.uniqueness import (
    room_duplicate_label_records,
    uniqueness_rules,
)


def test_uniqueness_rules_include_room_duplicate_label_control() -> None:
    assert "DQ-ROM-UNI-001" in uniqueness_rules()


def test_room_duplicate_detection_flags_only_one_duplicate_pair() -> None:
    connection = _room_connection(
        [
            ("ROOM-0001", "BLD-001", "Consultation 1"),
            ("ROOM-0002", "BLD-001", " Consultation 1 "),
            ("ROOM-0003", "BLD-001", "Treatment 1"),
            ("ROOM-0004", "BLD-002", "Consultation 1"),
        ]
    )
    try:
        duplicates = room_duplicate_label_records(connection)
    finally:
        connection.close()

    assert [row["room_id"] for row in duplicates] == ["ROOM-0001", "ROOM-0002"]
    assert {row["duplicate_group_key"] for row in duplicates} == {"BLD-001|consultation 1"}


def test_room_duplicate_detection_flags_multiple_independent_groups() -> None:
    connection = _room_connection(
        [
            ("ROOM-0001", "BLD-001", "Consultation 1"),
            ("ROOM-0002", "BLD-001", "Consultation 1"),
            ("ROOM-0003", "BLD-001", "Treatment 1"),
            ("ROOM-0004", "BLD-001", "Treatment 1"),
            ("ROOM-0005", "BLD-002", "Treatment 1"),
        ]
    )
    try:
        duplicates = room_duplicate_label_records(connection)
    finally:
        connection.close()

    assert [row["room_id"] for row in duplicates] == [
        "ROOM-0001",
        "ROOM-0002",
        "ROOM-0003",
        "ROOM-0004",
    ]


def test_room_duplicate_detection_returns_no_rows_without_duplicate_group() -> None:
    connection = _room_connection(
        [
            ("ROOM-0001", "BLD-001", "Consultation 1"),
            ("ROOM-0002", "BLD-002", "Consultation 1"),
            ("ROOM-0003", "BLD-001", "Treatment 1"),
        ]
    )
    try:
        duplicates = room_duplicate_label_records(connection)
    finally:
        connection.close()

    assert duplicates == []


def _room_connection(rows: list[tuple[str, str, str]]) -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute(
        """
        CREATE TABLE staging_rooms (
            room_id TEXT,
            building_id TEXT,
            room_name TEXT,
            normalised_name TEXT
        )
        """
    )
    connection.executemany(
        """
        INSERT INTO staging_rooms (room_id, building_id, room_name, normalised_name)
        VALUES (?, ?, ?, LOWER(TRIM(?)))
        """,
        [(room_id, building_id, room_name, room_name) for room_id, building_id, room_name in rows],
    )
    return connection
