from pathlib import Path


def test_communication_outputs_do_not_claim_approval_or_real_meetings() -> None:
    output_dir = Path("outputs/communication")
    combined = "\n".join(
        path.read_text() for path in output_dir.glob("*") if path.is_file()
    ).lower()

    assert "not_approved" in combined
    assert "no final recommendation" in combined
    assert "synthetic challenge scenario" in combined
    assert "board approved" not in combined
    assert "stakeholders agreed" not in combined
    assert "must implement" not in combined
    assert "guaranteed savings" not in combined.replace("no guaranteed savings", "")


def test_communication_outputs_retain_simulation_and_financial_caveats() -> None:
    text = Path("outputs/communication/executive_options_paper.md").read_text()
    finance = Path("outputs/communication/finance_brief.md").read_text()

    assert "All `24` simulated resilience rows failed" in text
    assert "not realisable without mitigation" in text
    assert "risk-adjusted NPV remains `0.0`" in finance
