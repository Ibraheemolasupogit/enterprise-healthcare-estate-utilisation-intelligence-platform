import sqlite3
from pathlib import Path

import pytest

from estate_intelligence.forecasting.engine import run_forecasting
from estate_intelligence.ingestion.loader import build_curated_database
from estate_intelligence.metrics.engine import calculate_utilisation
from estate_intelligence.optimisation.engine import run_optimisation
from estate_intelligence.scenarios.engine import run_scenarios
from estate_intelligence.simulation.engine import run_simulation, verify_simulation
from estate_intelligence.validation.engine import run_data_quality


def test_simulation_evidence_database_counts_and_immutability(tmp_path: Path) -> None:
    database = tmp_path / "simulation.db"
    _upstream(database)
    before = _core_counts(database)

    run_simulation(database_path=database, output_dir=None, rebuild=True)

    summary = verify_simulation(database)
    after = _core_counts(database)
    assert summary["case_count"] == 4
    assert summary["experiment_count"] == 6
    assert summary["replication_rows"] == 720
    assert before == after
    with sqlite3.connect(database) as connection:
        assert (
            connection.execute("SELECT COUNT(*) FROM evidence_simulation_summary").fetchone()[0]
            == 24
        )
        assert (
            connection.execute(
                "SELECT COUNT(*) FROM evidence_simulation_threshold_results"
            ).fetchone()[0]
            == 168
        )
        assert (
            connection.execute("SELECT COUNT(*) FROM evidence_simulation_failures").fetchone()[0]
            > 0
        )


def test_simulation_safe_overwrite_refusal(tmp_path: Path) -> None:
    database = tmp_path / "simulation-overwrite.db"
    _upstream(database)
    run_simulation(database_path=database, output_dir=None, rebuild=True)

    with pytest.raises(FileExistsError):
        run_simulation(database_path=database, output_dir=None, rebuild=False)


def _upstream(database: Path) -> None:
    build_curated_database(input_dir=Path("data/sample"), database_path=database, rebuild=True)
    run_data_quality(database_path=database, output_dir=None, rebuild=True)
    calculate_utilisation(database_path=database, output_dir=None, rebuild=True)
    run_forecasting(database_path=database, output_dir=None, rebuild=True)
    run_scenarios(database_path=database, output_dir=None, rebuild=True)
    run_optimisation(database_path=database, output_dir=None, rebuild=True)


def _core_counts(database: Path) -> dict[str, int]:
    tables = [
        "source_rooms",
        "source_bookings",
        "source_clinical_activity",
        "staging_rooms",
        "staging_bookings",
        "staging_clinical_activity",
        "curated_rooms",
        "curated_bookings",
        "curated_clinical_activity",
    ]
    with sqlite3.connect(database) as connection:
        return {
            table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in tables
        }
