from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_database_config_contract() -> None:
    document = yaml.safe_load((ROOT / "config" / "database.yaml").read_text(encoding="utf-8"))

    assert document["engine"] == "sqlite"
    assert document["database"]["path"] == "data/processed/estate_intelligence.db"
    assert document["table_prefixes"] == {
        "source": "source",
        "staging": "staging",
        "curated": "curated",
        "evidence": "evidence",
    }


def test_sql_assets_exist_and_views_do_not_select_star() -> None:
    schema_files = sorted((ROOT / "database" / "schema").glob("*.sql"))
    view_files = sorted((ROOT / "database" / "views").glob("*.sql"))

    assert len(schema_files) == 14
    assert len(view_files) == 7
    assert all("SELECT *" not in path.read_text(encoding="utf-8").upper() for path in view_files)
