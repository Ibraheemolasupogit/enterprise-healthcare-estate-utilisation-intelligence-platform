import sqlite3
from pathlib import Path

from estate_intelligence.reporting.audience import load_audiences
from estate_intelligence.reporting.challenge import build_objections
from estate_intelligence.reporting.evidence import resolve_run_lineage
from estate_intelligence.reporting.options import build_options
from estate_intelligence.reporting.service import (
    _build_claims,
    _build_run,
    _load_analytical_evidence,
    load_communication_config,
)


def test_claim_mapping_covers_major_claims(dashboard_database: Path) -> None:
    config = load_communication_config(Path("config/communication.yaml"))
    connection = sqlite3.connect(dashboard_database)
    connection.row_factory = sqlite3.Row
    lineage = resolve_run_lineage(connection)
    analytical = _load_analytical_evidence(connection, lineage)
    options = build_options(
        list(config.document["option_catalogue"]),
        analytical["financial_base"],
        analytical["scenario_comparison"],
        analytical["optimisation_comparison"],
    )
    run = _build_run(
        config,
        lineage,
        load_audiences(config.document),
        options,
        build_objections(list(config.document["challenge_catalogue"])),
    )
    claims = _build_claims(run, analytical, options)

    assert len(claims) >= 9
    assert {claim.source_table for claim in claims} >= {
        "evidence_simulation_summary",
        "evidence_financial_comparison",
        "evidence_optimisation_building_status",
    }
