import sqlite3
from pathlib import Path

from estate_intelligence.ingestion.loader import build_curated_database
from estate_intelligence.metrics.engine import calculate_utilisation, verify_utilisation
from estate_intelligence.validation.engine import run_data_quality


def test_utilisation_pipeline_quality_gates_known_records(tmp_path: Path) -> None:
    database = tmp_path / "estate.db"
    export_dir = tmp_path / "utilisation"
    build_curated_database(input_dir=Path("data/sample"), database_path=database, rebuild=True)
    run_data_quality(database_path=database, rebuild=True)

    summary = calculate_utilisation(database_path=database, output_dir=export_dir, rebuild=True)
    verified = verify_utilisation(database)

    assert summary["utilisation_run_id"].startswith("UTL-")
    assert summary["summary"]["available_hours"] > 0
    assert verified["room_count"] == 54
    assert verified["exclusion_count"] > 4
    assert (export_dir / "utilisation_run_summary.json").is_file()

    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    try:
        exclusions = {
            row["record_identifier"]
            for row in connection.execute(
                "SELECT record_identifier FROM evidence_analytics_exclusions"
            )
        }
        retained = {
            row["record_identifier"]: row["analytical_status"]
            for row in connection.execute(
                """
                SELECT record_identifier, analytical_status
                FROM evidence_analytics_population
                WHERE record_identifier IN ('ROOM-0018', 'WRK-00007')
                """
            )
        }
        duplicate_room_issues = [
            row["room_id"]
            for row in connection.execute(
                "SELECT room_id FROM evidence_room_utilisation ORDER BY room_id"
            )
            if row["room_id"] in {"ROOM-0002", "ROOM-0026"}
        ]
    finally:
        connection.close()

    assert {"ROOM-0002", "ROOM-0026", "BOOK-000025", "FIN-00002"}.issubset(exclusions)
    assert retained == {"ROOM-0018": "included", "WRK-00007": "included"}
    assert duplicate_room_issues == []


def test_utilisation_rebuild_does_not_duplicate_evidence(tmp_path: Path) -> None:
    database = tmp_path / "estate.db"
    build_curated_database(input_dir=Path("data/sample"), database_path=database, rebuild=True)
    run_data_quality(database_path=database, rebuild=True)

    first = calculate_utilisation(database_path=database, rebuild=True)
    second = calculate_utilisation(database_path=database, rebuild=True)

    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    try:
        run_count = connection.execute(
            "SELECT COUNT(*) AS count FROM evidence_utilisation_runs"
        ).fetchone()["count"]
    finally:
        connection.close()

    assert first["utilisation_run_id"] == second["utilisation_run_id"]
    assert run_count == 1
