"""Uniqueness rule helpers."""

from __future__ import annotations

import sqlite3
from typing import Any

from estate_intelligence.validation.rules import build_rule_catalogue


def uniqueness_rules() -> list[str]:
    """Return enabled uniqueness rule identifiers."""

    return [rule.rule_id for rule in build_rule_catalogue() if rule.dimension == "uniqueness"]


def room_duplicate_label_records(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    """Return room records in duplicate building/name groups."""

    rows = connection.execute(
        """
        WITH room_keys AS (
            SELECT
                room_id,
                building_id,
                room_name,
                COALESCE(NULLIF(normalised_name, ''), LOWER(TRIM(room_name))) AS room_key
            FROM staging_rooms
            WHERE room_name IS NOT NULL AND TRIM(room_name) <> ''
        ),
        duplicate_groups AS (
            SELECT building_id, room_key, COUNT(*) AS record_count
            FROM room_keys
            GROUP BY building_id, room_key
            HAVING COUNT(*) > 1
        )
        SELECT
            room_keys.room_id,
            room_keys.building_id,
            room_keys.room_name,
            room_keys.room_key,
            duplicate_groups.record_count,
            room_keys.building_id || '|' || room_keys.room_key AS duplicate_group_key
        FROM room_keys
        INNER JOIN duplicate_groups
            ON room_keys.building_id = duplicate_groups.building_id
            AND room_keys.room_key = duplicate_groups.room_key
        ORDER BY room_keys.building_id, room_keys.room_key, room_keys.room_id
        """
    ).fetchall()
    return [dict(row) for row in rows]
