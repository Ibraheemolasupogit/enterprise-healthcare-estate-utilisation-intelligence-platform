from pathlib import Path

import pytest


def generated_output_dir() -> Path:
    output_dir = Path("outputs/communication")
    required = output_dir / "executive_options_paper.md"
    if not required.is_file():
        pytest.skip("Generated communication evidence is absent; run make assurance-full.")
    return output_dir


def test_communication_outputs_do_not_claim_approval_or_real_meetings() -> None:
    output_dir = generated_output_dir()
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
    output_dir = generated_output_dir()
    text = (output_dir / "executive_options_paper.md").read_text()
    finance = (output_dir / "finance_brief.md").read_text()

    assert "All `24` simulated resilience rows failed" in text
    assert "not realisable without mitigation" in text
    assert "risk-adjusted NPV remains `0.0`" in finance
