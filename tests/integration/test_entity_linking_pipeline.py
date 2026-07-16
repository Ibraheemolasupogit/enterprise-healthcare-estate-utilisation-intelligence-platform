import sqlite3
from pathlib import Path

from estate_intelligence.ingestion.loader import build_curated_database


def test_linkage_results_are_exact_and_parent_aware(tmp_path: Path) -> None:
    database = tmp_path / "estate.db"
    build_curated_database(input_dir=Path("data/sample"), database_path=database, rebuild=True)
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    try:
        rooms = connection.execute(
            "SELECT COUNT(*) AS count FROM evidence_linkage_results WHERE entity_type='room'"
        ).fetchone()["count"]
        warnings = connection.execute(
            "SELECT COUNT(*) AS count FROM evidence_linkage_results "
            "WHERE match_status='matched_with_warning'"
        ).fetchone()["count"]
        sites = connection.execute("SELECT COUNT(*) AS count FROM curated_sites").fetchone()[
            "count"
        ]
    finally:
        connection.close()

    assert rooms == 56
    assert warnings == 1
    assert sites == 4
