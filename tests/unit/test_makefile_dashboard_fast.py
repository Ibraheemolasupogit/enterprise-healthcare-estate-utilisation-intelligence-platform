from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_fast_assurance_uses_dashboard_fast_check_not_canonical_database_check() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")

    assert "dashboard-check-fast:" in makefile
    assert "assurance-fast:" in makefile
    assurance_fast_line = next(
        line for line in makefile.splitlines() if line.startswith("assurance-fast:")
    )
    assert "dashboard-check-fast" in assurance_fast_line
    assert "dashboard-check " not in assurance_fast_line
    assert "verify-communication-evidence" not in assurance_fast_line
    assert "run-assurance" not in assurance_fast_line
    assert "verify-assurance" not in assurance_fast_line


def test_full_assurance_retains_canonical_dashboard_check() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    full_assurance_line = next(
        line for line in makefile.splitlines() if line.startswith("assurance-full:")
    )

    assert "dashboard-check" in full_assurance_line
    assert "verify-communication-evidence" in full_assurance_line
    assert "run-assurance" in full_assurance_line
    assert "verify-assurance" in full_assurance_line
