import sqlite3
from pathlib import Path

from estate_intelligence.ingestion.loader import build_curated_database
from estate_intelligence.metrics.engine import calculate_utilisation
from estate_intelligence.validation.engine import run_data_quality


def test_utilisation_evidence_database_counts_and_immutability(tmp_path: Path) -> None:
    database = tmp_path / "estate.db"
    build_curated_database(input_dir=Path("data/sample"), database_path=database, rebuild=True)
    run_data_quality(database_path=database, rebuild=True)

    before = _table_counts(database)
    calculate_utilisation(database_path=database, rebuild=True)
    after = _table_counts(database)

    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    try:
        counts = {
            table: connection.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()["count"]
            for table in (
                "evidence_utilisation_runs",
                "evidence_analytics_population",
                "evidence_analytics_exclusions",
                "evidence_room_utilisation",
                "evidence_building_utilisation",
                "evidence_site_utilisation",
                "evidence_service_utilisation",
                "evidence_time_band_utilisation",
                "evidence_monthly_utilisation",
                "evidence_underutilisation_flags",
                "evidence_unit_cost_metrics",
            )
        }
        manual = [
            row["record_identifier"]
            for row in connection.execute(
                """
                SELECT record_identifier
                FROM evidence_analytics_exclusions
                WHERE reason='manual_review_excluded_by_policy'
                ORDER BY record_identifier
                """
            )
        ]
    finally:
        connection.close()

    assert before == after
    assert counts["evidence_utilisation_runs"] == 1
    assert counts["evidence_analytics_population"] == 2987
    assert counts["evidence_room_utilisation"] == 54
    assert counts["evidence_building_utilisation"] == 8
    assert counts["evidence_site_utilisation"] == 4
    assert counts["evidence_service_utilisation"] == 12
    assert counts["evidence_unit_cost_metrics"] == 8
    assert manual == ["BOOK-000025", "FIN-00002", "ROOM-0002", "ROOM-0026"]


def _table_counts(database: Path) -> dict[str, int]:
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    try:
        return {
            table: connection.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()["count"]
            for table in (
                "source_rooms",
                "staging_rooms",
                "curated_rooms",
                "source_bookings",
                "staging_bookings",
                "curated_bookings",
            )
        }
    finally:
        connection.close()
