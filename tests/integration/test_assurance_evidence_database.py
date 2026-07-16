import sqlite3
from pathlib import Path

from estate_intelligence.assurance.pipeline import run_assurance


def test_assurance_pipeline_persists_database_tables(tmp_path: Path) -> None:
    database = Path("data/processed/estate_intelligence.db")
    run_assurance(database, Path("config/assurance.yaml"), tmp_path, "canonical", rebuild=True)
    connection = sqlite3.connect(database)
    try:
        counts = {
            table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in [
                "evidence_assurance_runs",
                "evidence_assurance_check_catalogue",
                "evidence_assurance_check_results",
                "evidence_assurance_release_gates",
                "evidence_assurance_manifests",
            ]
        }
    finally:
        connection.close()

    assert counts == {
        "evidence_assurance_runs": 1,
        "evidence_assurance_check_catalogue": 18,
        "evidence_assurance_check_results": 18,
        "evidence_assurance_release_gates": 8,
        "evidence_assurance_manifests": 14,
    }
