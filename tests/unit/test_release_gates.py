from estate_intelligence.assurance.catalogue import build_check_catalogue
from estate_intelligence.assurance.models import AssuranceResult
from estate_intelligence.assurance.release import build_release_gates, release_readiness


def test_release_gates_preserve_conditional_engineering_readiness() -> None:
    results = [
        AssuranceResult(
            check, "pass_with_warnings" if check.category == "simulation" else "pass", "ok", "x"
        )
        for check in build_check_catalogue()
    ]
    gates = build_release_gates(results)

    assert len(gates) == 8
    assert any(gate.status == "conditional_pass" for gate in gates)
    assert release_readiness(gates) == "engineering_ready_with_conditions"
