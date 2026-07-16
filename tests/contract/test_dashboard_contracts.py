from pathlib import Path

DASHBOARD_FILES = list(Path("dashboard").glob("**/*.py"))


def test_dashboard_contract_has_no_approval_or_real_patient_claims() -> None:
    combined = "\n".join(path.read_text().lower() for path in DASHBOARD_FILES)

    assert "no real patient or estate data" in combined
    assert "no estate decision is approved" in combined
    assert "implementation recommendation" in combined
    assert "recommended scenario" not in combined
    assert "no external apis" in combined


def test_dashboard_contract_keeps_simulation_and_financial_warnings_visible() -> None:
    combined = "\n".join(path.read_text() for path in DASHBOARD_FILES)

    assert "All cases are not realisable without mitigation" in combined
    assert "All {len(data['resilience'])} case/experiment resilience rows failed" in combined
    assert "Mathematical optimality is not operational approval" in combined
    assert "Positive nominal NPV does not override" in combined
