from pathlib import Path

import pytest

from estate_intelligence.ingestion.database import connect, safe_database_path
from estate_intelligence.ingestion.writer import safe_export_dir


def test_database_path_safety(tmp_path: Path) -> None:
    assert safe_database_path(tmp_path / "estate.db") == tmp_path / "estate.db"
    with pytest.raises(ValueError, match="unsafe"):
        safe_database_path(Path("/etc/estate.db"))
    with pytest.raises(ValueError, match="SQLite"):
        safe_database_path(tmp_path / "estate.txt")


def test_database_path_rejects_tmp_path_outside_test_mode(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("ESTATE_INTELLIGENCE_TEST_MODE", raising=False)

    with pytest.raises(ValueError, match="unsafe"):
        safe_database_path(tmp_path / "estate.db")


def test_database_path_allows_canonical_repository_path_outside_test_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("ESTATE_INTELLIGENCE_TEST_MODE", raising=False)

    assert safe_database_path(Path("data/processed/estate.db")).name == "estate.db"


def test_database_path_rejects_traversal_outside_approved_roots(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("ESTATE_INTELLIGENCE_TEST_MODE", raising=False)

    with pytest.raises(ValueError, match="unsafe"):
        safe_database_path(Path("data/processed/../../outside.db"))


def test_export_dir_allows_tmp_path_in_test_mode(tmp_path: Path) -> None:
    assert safe_export_dir(tmp_path / "evidence") == tmp_path / "evidence"


def test_export_dir_rejects_tmp_path_outside_test_mode(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("ESTATE_INTELLIGENCE_TEST_MODE", raising=False)

    with pytest.raises(ValueError, match="unsafe"):
        safe_export_dir(tmp_path / "evidence")


def test_export_dir_allows_canonical_repository_outputs_outside_test_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("ESTATE_INTELLIGENCE_TEST_MODE", raising=False)

    assert safe_export_dir(Path("outputs/ingestion")).name == "ingestion"
    assert safe_export_dir(Path("outputs/financial/reports")).name == "reports"


def test_export_dir_rejects_traversal_outside_approved_roots(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("ESTATE_INTELLIGENCE_TEST_MODE", raising=False)

    with pytest.raises(ValueError, match="unsafe"):
        safe_export_dir(Path("outputs/ingestion/../../outside"))


def test_sqlite_foreign_keys_enabled(tmp_path: Path) -> None:
    connection = connect(tmp_path / "estate.db")
    try:
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    finally:
        connection.close()
