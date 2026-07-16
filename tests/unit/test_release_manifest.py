from estate_intelligence.assurance.pipeline import BOUNDARY_STATEMENT
from estate_intelligence.assurance.reproducibility import stable_json


def test_release_boundary_statement_is_explicit() -> None:
    payload = {"boundary": BOUNDARY_STATEMENT}

    assert "does not constitute governance approval" in stable_json(payload)
    assert "operational implementation readiness" in BOUNDARY_STATEMENT
