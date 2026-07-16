import sqlite3
from pathlib import Path

from estate_intelligence.reporting.evidence import resolve_run_lineage
from estate_intelligence.reporting.options import build_options
from estate_intelligence.reporting.service import (
    _load_analytical_evidence,
    load_communication_config,
)


def test_option_catalogue_is_complete_and_not_approved() -> None:
    config = load_communication_config(Path("config/communication.yaml"))
    connection = sqlite3.connect("data/processed/estate_intelligence.db")
    connection.row_factory = sqlite3.Row
    lineage = resolve_run_lineage(connection)
    analytical = _load_analytical_evidence(connection, lineage)

    options = build_options(
        list(config.document["option_catalogue"]),
        analytical["financial_base"],
        analytical["scenario_comparison"],
        analytical["optimisation_comparison"],
    )

    assert [option.option_id for option in options] == [
        "OPT-A",
        "OPT-B",
        "OPT-C",
        "OPT-D",
        "OPT-E",
        "OPT-F",
        "OPT-G",
    ]
    assert all(option.implementation_status == "not_approved" for option in options)
    assert max(option.nominal_npv for option in options) > 0
    assert max(option.risk_adjusted_npv for option in options) == 0
