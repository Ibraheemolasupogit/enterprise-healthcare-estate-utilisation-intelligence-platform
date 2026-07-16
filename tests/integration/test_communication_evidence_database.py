import sqlite3


def test_communication_evidence_database_rows_are_persisted() -> None:
    connection = sqlite3.connect("data/processed/estate_intelligence.db")

    counts = {
        table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in [
            "evidence_communication_runs",
            "evidence_communication_audiences",
            "evidence_communication_options",
            "evidence_communication_objections",
            "evidence_communication_challenges",
            "evidence_communication_revisions",
            "evidence_communication_claims",
            "evidence_communication_decision_records",
            "evidence_communication_products",
            "evidence_communication_provenance",
        ]
    }

    assert counts["evidence_communication_audiences"] == 5
    assert counts["evidence_communication_options"] == 7
    assert counts["evidence_communication_revisions"] >= 1
    assert counts["evidence_communication_claims"] >= 9
