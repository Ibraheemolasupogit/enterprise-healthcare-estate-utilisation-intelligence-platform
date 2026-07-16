"""Release gate construction."""

from __future__ import annotations

from typing import cast

from estate_intelligence.assurance.models import AssuranceResult, GateStatus, ReleaseGate

GATES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("GATE-QUALITY", "Quality", ("repository", "python_quality", "configuration", "sql")),
    ("GATE-DATA", "Data", ("synthetic_data", "ingestion", "data_quality", "utilisation")),
    (
        "GATE-ANALYTICS",
        "Analytics",
        ("forecasting", "scenarios", "optimisation", "simulation", "financial"),
    ),
    ("GATE-REPRODUCIBILITY", "Reproducibility", ("release",)),
    ("GATE-DASHBOARD", "Dashboard", ("dashboard",)),
    ("GATE-COMMUNICATION", "Communication", ("communication",)),
    ("GATE-DOCUMENTATION", "Documentation", ("documentation",)),
    ("GATE-SECURITY", "Security", ("security",)),
)


def build_release_gates(results: list[AssuranceResult]) -> list[ReleaseGate]:
    by_category = {result.check.category: result.status for result in results}
    gates: list[ReleaseGate] = []
    for gate_id, gate_name, categories in GATES:
        statuses = [by_category.get(category, "not_run") for category in categories]
        if "fail" in statuses or "not_run" in statuses:
            status = "fail"
            conditions = "Required assurance checks must pass before use."
        elif "pass_with_warnings" in statuses:
            status = "conditional_pass"
            conditions = (
                "Engineering evidence is usable with recorded synthetic and readiness caveats."
            )
        else:
            status = "pass"
            conditions = "No additional engineering condition."
        gates.append(
            ReleaseGate(
                gate_id=gate_id,
                gate_name=gate_name,
                status=cast(GateStatus, status),
                conditions=conditions,
                evidence_source="evidence_assurance_check_results",
            )
        )
    return gates


def release_readiness(gates: list[ReleaseGate]) -> str:
    statuses = {gate.status for gate in gates}
    if "fail" in statuses or "not_evaluated" in statuses:
        return "not_engineering_ready"
    if "conditional_pass" in statuses:
        return "engineering_ready_with_conditions"
    return "engineering_ready"
