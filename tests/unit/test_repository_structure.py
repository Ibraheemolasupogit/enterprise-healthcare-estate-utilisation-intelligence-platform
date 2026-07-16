from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

TOP_LEVEL_FILES = {
    ".dockerignore",
    ".env.example",
    ".gitignore",
    ".markdownlint.json",
    "LICENSE",
    "Makefile",
    "README.md",
    "pyproject.toml",
    "requirements-dev.txt",
}

REQUIRED_DIRS = {
    ".github/ISSUE_TEMPLATE",
    ".github/workflows",
    "config/environments",
    "data/raw",
    "data/staged",
    "data/processed",
    "data/reference",
    "data/sample",
    "data/outputs",
    "database/schema",
    "database/seeds",
    "database/views",
    "dashboard/components",
    "dashboard/pages",
    "docs",
    "handover",
    "infrastructure/deployment",
    "infrastructure/docker",
    "outputs",
    "portfolio/diagrams",
    "portfolio/manifests",
    "portfolio/screenshots",
    "powerbi/datasets",
    "powerbi/measures",
    "powerbi/screenshots",
    "reports/estates",
    "reports/executive",
    "reports/finance",
    "reports/operational",
    "reports/sample",
    "reports/scenarios",
    "reports/technical",
    "scripts",
    "src/estate_intelligence",
    "stakeholder_evidence",
    "tests/contract",
    "tests/end_to_end",
    "tests/fixtures",
    "tests/integration",
    "tests/unit",
}

DOCS = {
    "architecture.md",
    "backlog.md",
    "business_problem.md",
    "communicating_and_influencing_model.md",
    "data_quality_framework.md",
    "data_quality_rules.md",
    "data_quality_scoring.md",
    "database_design.md",
    "decision_criteria.md",
    "analytical_population.md",
    "effective_utilisation.md",
    "forecasting_methodology.md",
    "forecast_series.md",
    "forecast_eligibility.md",
    "time_series_validation.md",
    "forecast_model_selection.md",
    "forecast_uncertainty.md",
    "ingestion_pipeline.md",
    "linkage_quality.md",
    "limitations.md",
    "manual_review_process.md",
    "mvp_scope.md",
    "persistent_underutilisation.md",
    "reconciliation_methodology.md",
    "roadmap.md",
    "stakeholder_map.md",
    "unit_cost_methodology.md",
    "utilisation_methodology.md",
    "utilisation_definitions.md",
    "scenario_methodology.md",
    "scenario_catalogue.md",
    "scenario_constraints.md",
    "scenario_scoring.md",
    "scenario_uncertainty.md",
    "scenario_cost_methodology.md",
    "optimisation_methodology.md",
    "optimisation_variables.md",
    "optimisation_constraints.md",
    "optimisation_objective.md",
    "optimisation_solver.md",
    "optimisation_infeasibility.md",
    "simulation_methodology.md",
    "simulation_arrivals.md",
    "simulation_service_times.md",
    "simulation_resources.md",
    "simulation_experiments.md",
    "simulation_resilience.md",
    "simulation_uncertainty.md",
    "financial_methodology.md",
    "financial_cost_model.md",
    "financial_cashflows.md",
    "financial_payback_npv.md",
    "financial_sensitivity.md",
    "financial_risk_adjustment.md",
    "financial_break_even.md",
    "audience_briefing_strategy.md",
    "challenge_response_methodology.md",
    "communication_framework.md",
    "communication_language_controls.md",
    "decision_record_methodology.md",
    "evidence_to_claim_mapping.md",
    "assurance_framework.md",
    "ci_cd_strategy.md",
    "release_gates.md",
    "reproducibility_assurance.md",
    "security_assurance.md",
    "release_evidence.md",
    "developer_quality_workflow.md",
    "repository_structure.md",
    "final_milestone_audit.md",
    "technical_decisions.md",
    "evidence_index.md",
}

CONFIGS = {
    "settings.yaml",
    "data_contracts.yaml",
    "utilisation_thresholds.yaml",
    "utilisation.yaml",
    "forecasting.yaml",
    "scenarios.yaml",
    "optimisation.yaml",
    "simulation.yaml",
    "finance.yaml",
    "communication.yaml",
    "assurance.yaml",
    "portfolio.yaml",
    "risk_thresholds.yaml",
    "data_quality.yaml",
    "environments/development.yaml",
    "environments/staging.yaml",
    "environments/production.yaml",
}

PACKAGE_FILES = {
    "__init__.py",
    "cli.py",
    "settings.py",
    "utils/__init__.py",
    "utils/logging.py",
    "utils/paths.py",
}

BOUNDARY_PACKAGES = {
    "financial",
    "forecasting",
    "optimisation",
    "recommendations",
    "reporting",
    "risk",
    "scenarios",
    "simulation",
    "assurance",
    "portfolio",
}

SYNTHETIC_DATA_FILES = {
    "__init__.py",
    "accessibility.py",
    "bookings.py",
    "buildings.py",
    "clinical_activity.py",
    "common.py",
    "finance.py",
    "generator.py",
    "metadata.py",
    "models.py",
    "rooms.py",
    "services.py",
    "workforce.py",
}

INGESTION_FILES = {
    "__init__.py",
    "database.py",
    "loader.py",
    "manifest.py",
    "models.py",
    "schema.py",
    "source_registry.py",
    "writer.py",
}

LINKING_FILES = {
    "__init__.py",
    "building_linker.py",
    "common.py",
    "duplicate_detector.py",
    "linkage_quality.py",
    "models.py",
    "normalisation.py",
    "room_linker.py",
    "service_linker.py",
    "site_linker.py",
}

VALIDATION_FILES = {
    "__init__.py",
    "catalogue.py",
    "completeness.py",
    "consistency.py",
    "engine.py",
    "ingestion_checks.py",
    "models.py",
    "reconciliation.py",
    "referential_checks.py",
    "reporting.py",
    "rules.py",
    "schema_checks.py",
    "scoring.py",
    "timeliness.py",
    "uniqueness.py",
    "validity.py",
}

METRICS_FILES = {
    "__init__.py",
    "activity.py",
    "availability.py",
    "engine.py",
    "finance.py",
    "models.py",
    "reporting.py",
    "scoring.py",
    "time_bands.py",
    "utilisation.py",
    "workforce.py",
}

FORECASTING_FILES = {
    "__init__.py",
    "aggregation.py",
    "backtesting.py",
    "baseline.py",
    "eligibility.py",
    "engine.py",
    "evaluation.py",
    "exponential_smoothing.py",
    "intervals.py",
    "models.py",
    "reporting.py",
    "selection.py",
    "series.py",
}

OPTIMISATION_FILES = {
    "__init__.py",
    "candidates.py",
    "constraints.py",
    "diagnostics.py",
    "engine.py",
    "model.py",
    "models.py",
    "objective.py",
    "reporting.py",
    "results.py",
    "solver.py",
    "variables.py",
}

SIMULATION_FILES = {
    "__init__.py",
    "arrivals.py",
    "engine.py",
    "events.py",
    "experiments.py",
    "models.py",
    "reporting.py",
    "resources.py",
    "results.py",
    "scenarios.py",
    "seeds.py",
    "service_times.py",
    "validation.py",
}

FINANCIAL_FILES = {
    "__init__.py",
    "assumptions.py",
    "break_even.py",
    "cashflows.py",
    "costs.py",
    "engine.py",
    "models.py",
    "npv.py",
    "payback.py",
    "reporting.py",
    "risk_adjustment.py",
    "scenarios.py",
    "sensitivity.py",
    "validation.py",
}

REPORTING_FILES = {
    "__init__.py",
    "audience.py",
    "challenge.py",
    "clinical.py",
    "decision_record.py",
    "estates.py",
    "evidence.py",
    "executive.py",
    "finance.py",
    "models.py",
    "options.py",
    "provenance.py",
    "rendering.py",
    "service.py",
    "technical.py",
}

ASSURANCE_FILES = {
    "__init__.py",
    "catalogue.py",
    "checks.py",
    "evidence.py",
    "manifest.py",
    "models.py",
    "pipeline.py",
    "release.py",
    "reporting.py",
    "reproducibility.py",
    "security.py",
    "validation.py",
}

PORTFOLIO_FILES = {
    "__init__.py",
    "manifest.py",
    "models.py",
    "service.py",
    "validation.py",
}


def test_required_top_level_files_exist() -> None:
    missing = [path for path in TOP_LEVEL_FILES if not (ROOT / path).is_file()]
    assert missing == []


def test_required_directories_exist() -> None:
    missing = [path for path in REQUIRED_DIRS if not (ROOT / path).is_dir()]
    assert missing == []


def test_expected_documentation_exists() -> None:
    missing = [path for path in DOCS if not (ROOT / "docs" / path).is_file()]
    assert missing == []


def test_expected_configuration_files_exist() -> None:
    missing = [path for path in CONFIGS if not (ROOT / "config" / path).is_file()]
    assert missing == []


def test_package_structure_is_foundation_only() -> None:
    package_root = ROOT / "src" / "estate_intelligence"
    missing = [path for path in PACKAGE_FILES if not (package_root / path).is_file()]
    assert missing == []

    for package in BOUNDARY_PACKAGES - {
        "financial",
        "forecasting",
        "scenarios",
        "optimisation",
        "simulation",
        "reporting",
        "assurance",
        "portfolio",
    }:
        files = sorted(path.name for path in (package_root / package).iterdir() if path.is_file())
        assert files == ["__init__.py"]

    synthetic_files = {
        path.name for path in (package_root / "synthetic_data").iterdir() if path.is_file()
    }
    assert synthetic_files == SYNTHETIC_DATA_FILES
    assert {
        path.name for path in (package_root / "ingestion").iterdir() if path.is_file()
    } == INGESTION_FILES
    assert {
        path.name for path in (package_root / "linking").iterdir() if path.is_file()
    } == LINKING_FILES
    assert {
        path.name for path in (package_root / "validation").iterdir() if path.is_file()
    } == VALIDATION_FILES
    assert {
        path.name for path in (package_root / "metrics").iterdir() if path.is_file()
    } == METRICS_FILES
    assert {
        path.name for path in (package_root / "forecasting").iterdir() if path.is_file()
    } == FORECASTING_FILES
    assert {path.name for path in (package_root / "scenarios").iterdir() if path.is_file()} == {
        "__init__.py",
        "baseline.py",
        "capacity.py",
        "comparison.py",
        "constraints.py",
        "engine.py",
        "evaluator.py",
        "hybrid_redesign.py",
        "light_consolidation.py",
        "models.py",
        "reporting.py",
        "site_consolidation.py",
        "uncertainty.py",
    }
    assert {
        path.name for path in (package_root / "optimisation").iterdir() if path.is_file()
    } == OPTIMISATION_FILES
    assert {
        path.name for path in (package_root / "simulation").iterdir() if path.is_file()
    } == SIMULATION_FILES
    assert {
        path.name for path in (package_root / "financial").iterdir() if path.is_file()
    } == FINANCIAL_FILES
    assert {
        path.name for path in (package_root / "reporting").iterdir() if path.is_file()
    } == REPORTING_FILES
    assert {
        path.name for path in (package_root / "assurance").iterdir() if path.is_file()
    } == ASSURANCE_FILES
    assert {
        path.name for path in (package_root / "portfolio").iterdir() if path.is_file()
    } == PORTFOLIO_FILES


def test_no_accidental_real_data_or_generated_evidence_files() -> None:
    evidence_roots = [
        ROOT / "data" / "raw",
        ROOT / "data" / "staged",
        ROOT / "data" / "processed",
        ROOT / "data" / "outputs",
        ROOT / "outputs",
        ROOT / "reports",
        ROOT / "powerbi" / "screenshots",
    ]
    unexpected = [
        path
        for evidence_root in evidence_roots
        for path in evidence_root.rglob("*")
        if path.is_file()
        and path.name != ".gitkeep"
        and "outputs/ingestion" not in path.as_posix()
        and "outputs/data_quality" not in path.as_posix()
        and "outputs/utilisation" not in path.as_posix()
        and "outputs/forecasting" not in path.as_posix()
        and "outputs/scenarios" not in path.as_posix()
        and "outputs/optimisation" not in path.as_posix()
        and "outputs/simulation" not in path.as_posix()
        and "outputs/financial" not in path.as_posix()
        and "outputs/communication" not in path.as_posix()
        and "outputs/assurance" not in path.as_posix()
        and not path.name.startswith("estate_intelligence")
        and path.suffix not in {".db", ".sqlite", ".sqlite3", ".db-shm", ".db-wal"}
    ]

    assert unexpected == []
