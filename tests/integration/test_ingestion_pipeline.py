import sqlite3
from pathlib import Path

from estate_intelligence.ingestion.loader import build_curated_database, verify_database


def test_build_curated_database_counts_and_issue_detection(tmp_path: Path) -> None:
    database = tmp_path / "estate.db"
    export_dir = tmp_path / "evidence"

    summary = build_curated_database(
        input_dir=Path("data/sample"),
        database_path=database,
        export_dir=export_dir,
        rebuild=True,
    )
    verified = verify_database(database)

    assert summary["source_rows"]["bookings"] == 1440
    assert verified["detected_issues"] == 5
    assert (export_dir / "reconciliation_summary.csv").is_file()


def test_rebuild_refusal(tmp_path: Path) -> None:
    database = tmp_path / "estate.db"
    build_curated_database(input_dir=Path("data/sample"), database_path=database, rebuild=True)

    try:
        build_curated_database(input_dir=Path("data/sample"), database_path=database, rebuild=False)
    except FileExistsError as exc:
        assert "without --rebuild" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected rebuild refusal")


def test_views_have_rows_and_no_metric_or_recommendation_columns(tmp_path: Path) -> None:
    database = tmp_path / "estate.db"
    build_curated_database(input_dir=Path("data/sample"), database_path=database, rebuild=True)
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    try:
        row_count = connection.execute(
            "SELECT COUNT(*) AS count FROM estate_decision_base_view"
        ).fetchone()["count"]
        columns = [
            row["name"]
            for row in connection.execute("PRAGMA table_info(estate_decision_base_view)")
        ]
    finally:
        connection.close()

    assert row_count == 56
    assert not any("utilisation" in column for column in columns)
    assert not any("recommendation" in column for column in columns)
