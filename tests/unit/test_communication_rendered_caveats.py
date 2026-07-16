from pathlib import Path

from estate_intelligence.reporting.rendering import write_csv, write_json, write_markdown


def test_fixture_rendered_outputs_retain_non_approval_and_caveats(tmp_path: Path) -> None:
    output_dir = tmp_path / "communication"
    write_markdown(
        output_dir / "executive_options_paper.md",
        """
        Synthetic challenge scenario.
        decision_status: awaiting_governance_decision
        approval_status: not_approved
        All simulated resilience rows failed.
        Financial cases are not realisable without mitigation.
        No final recommendation is made.
        """,
    )
    write_markdown(
        output_dir / "finance_brief.md",
        "risk-adjusted NPV remains `0.0`; no approval or implementation recommendation.",
    )
    write_json(
        output_dir / "decision_record.json",
        {
            "decision_status": "awaiting_governance_decision",
            "approval_status": "not_approved",
        },
    )
    write_csv(
        output_dir / "option_catalogue.csv",
        [{"option_id": "OPT-A", "implementation_status": "not_approved"}],
        ["option_id", "implementation_status"],
    )

    combined = "\n".join(path.read_text() for path in output_dir.iterdir()).lower()

    assert "not_approved" in combined
    assert "awaiting_governance_decision" in combined
    assert "all simulated resilience rows failed" in combined
    assert "not realisable without mitigation" in combined
    assert "board approved" not in combined
    assert "stakeholders agreed" not in combined
    assert "must implement" not in combined
