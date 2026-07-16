from pathlib import Path

from estate_intelligence.assurance.validation import validate_clean_schema, validate_migration_order

ROOT = Path(__file__).resolve().parents[2]


def test_sql_migrations_are_ordered_and_execute_cleanly() -> None:
    ordered, detail = validate_migration_order(ROOT / "database" / "schema")
    clean, clean_detail = validate_clean_schema(ROOT)

    assert ordered, detail
    assert clean, clean_detail
