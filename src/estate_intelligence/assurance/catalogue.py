"""Stable Milestone 13 assurance check catalogue."""

from __future__ import annotations

from estate_intelligence.assurance.models import AssuranceCheck

CHECK_DEFINITIONS: tuple[tuple[str, str, str, str], ...] = (
    ("ASR-REP-001", "repository", "Repository structure", "Required repository structure exists."),
    (
        "ASR-PY-001",
        "python_quality",
        "Python quality",
        "Ruff, format, mypy and tests are configured.",
    ),
    ("ASR-CFG-001", "configuration", "Configuration validation", "Required YAML configs parse."),
    ("ASR-SQL-001", "sql", "SQL migrations", "Migrations are ordered and executable."),
    (
        "ASR-DAT-001",
        "synthetic_data",
        "Synthetic data",
        "Canonical synthetic data is reproducible.",
    ),
    ("ASR-ING-001", "ingestion", "Ingestion evidence", "Ingestion run and evidence are present."),
    ("ASR-DQ-001", "data_quality", "Data-quality evidence", "Quality evidence preserves defects."),
    ("ASR-UTL-001", "utilisation", "Utilisation evidence", "Utilisation evidence is present."),
    ("ASR-FCT-001", "forecasting", "Forecasting evidence", "Forecasting evidence is present."),
    ("ASR-SCN-001", "scenarios", "Scenario evidence", "Scenario evidence is present."),
    ("ASR-OPT-001", "optimisation", "Optimisation evidence", "Optimisation evidence is present."),
    ("ASR-SIM-001", "simulation", "Simulation evidence", "Simulation failures remain visible."),
    ("ASR-FIN-001", "financial", "Financial evidence", "Financial caveats remain visible."),
    ("ASR-DSH-001", "dashboard", "Dashboard assurance", "Dashboard remains local and read-only."),
    (
        "ASR-COM-001",
        "communication",
        "Communication assurance",
        "Communication remains non-approving.",
    ),
    ("ASR-DOC-001", "documentation", "Documentation assurance", "Required docs exist and parse."),
    ("ASR-SEC-001", "security", "Security scan", "Local secret and workflow safety scan passes."),
    ("ASR-REL-001", "release", "Release readiness", "Release gates and manifest are complete."),
)


def build_check_catalogue() -> list[AssuranceCheck]:
    """Build the deterministic assurance check catalogue."""

    checks: list[AssuranceCheck] = []
    for check_id, category, name, description in CHECK_DEFINITIONS:
        checks.append(
            AssuranceCheck(
                check_id=check_id,
                category=category,
                name=name,
                description=description,
                severity="critical" if category in {"repository", "release"} else "major",
                required=True,
                command_or_method=f"assurance.{category}",
                expected_condition="Configured evidence and safety controls pass.",
                failure_action="Fix the failed assurance control before release evidence is used.",
                evidence_source="SQLite evidence and repository files",
            )
        )
    return checks
