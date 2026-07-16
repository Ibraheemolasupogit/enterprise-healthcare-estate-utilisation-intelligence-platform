CREATE TABLE IF NOT EXISTS evidence_assurance_runs (
    assurance_run_id TEXT PRIMARY KEY,
    framework_version TEXT NOT NULL,
    profile TEXT NOT NULL,
    ingestion_run_id TEXT NOT NULL,
    quality_run_id TEXT NOT NULL,
    utilisation_run_id TEXT NOT NULL,
    forecast_run_id TEXT NOT NULL,
    scenario_run_id TEXT NOT NULL,
    optimisation_run_id TEXT NOT NULL,
    simulation_run_id TEXT NOT NULL,
    financial_run_id TEXT NOT NULL,
    communication_run_id TEXT NOT NULL,
    config_checksum TEXT NOT NULL,
    catalogue_checksum TEXT NOT NULL,
    repository_contract_checksum TEXT NOT NULL,
    documentation_contract_checksum TEXT NOT NULL,
    security_rule_checksum TEXT NOT NULL,
    release_readiness_status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence_assurance_check_catalogue (
    assurance_run_id TEXT NOT NULL,
    check_id TEXT NOT NULL,
    category TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    severity TEXT NOT NULL,
    required INTEGER NOT NULL,
    command_or_method TEXT NOT NULL,
    expected_condition TEXT NOT NULL,
    failure_action TEXT NOT NULL,
    evidence_source TEXT NOT NULL,
    PRIMARY KEY (assurance_run_id, check_id)
);

CREATE TABLE IF NOT EXISTS evidence_assurance_check_results (
    assurance_run_id TEXT NOT NULL,
    check_id TEXT NOT NULL,
    category TEXT NOT NULL,
    status TEXT NOT NULL,
    severity TEXT NOT NULL,
    required INTEGER NOT NULL,
    expected_condition TEXT NOT NULL,
    observed_result TEXT NOT NULL,
    evidence_source TEXT NOT NULL,
    checksum TEXT NOT NULL,
    PRIMARY KEY (assurance_run_id, check_id)
);

CREATE TABLE IF NOT EXISTS evidence_assurance_failures (
    assurance_run_id TEXT NOT NULL,
    check_id TEXT NOT NULL,
    failure_action TEXT NOT NULL,
    observed_result TEXT NOT NULL,
    PRIMARY KEY (assurance_run_id, check_id)
);

CREATE TABLE IF NOT EXISTS evidence_assurance_warnings (
    assurance_run_id TEXT NOT NULL,
    warning_id TEXT NOT NULL,
    check_id TEXT NOT NULL,
    warning_text TEXT NOT NULL,
    condition TEXT NOT NULL,
    PRIMARY KEY (assurance_run_id, warning_id)
);

CREATE TABLE IF NOT EXISTS evidence_assurance_reproducibility (
    assurance_run_id TEXT NOT NULL,
    check_name TEXT NOT NULL,
    status TEXT NOT NULL,
    observed_result TEXT NOT NULL,
    checksum TEXT NOT NULL,
    PRIMARY KEY (assurance_run_id, check_name)
);

CREATE TABLE IF NOT EXISTS evidence_assurance_security_findings (
    assurance_run_id TEXT NOT NULL,
    finding_id TEXT NOT NULL,
    severity TEXT NOT NULL,
    status TEXT NOT NULL,
    file_path TEXT NOT NULL,
    finding_summary TEXT NOT NULL,
    PRIMARY KEY (assurance_run_id, finding_id)
);

CREATE TABLE IF NOT EXISTS evidence_assurance_documentation_results (
    assurance_run_id TEXT NOT NULL,
    document_path TEXT NOT NULL,
    status TEXT NOT NULL,
    observed_result TEXT NOT NULL,
    checksum TEXT NOT NULL,
    PRIMARY KEY (assurance_run_id, document_path)
);

CREATE TABLE IF NOT EXISTS evidence_assurance_release_gates (
    assurance_run_id TEXT NOT NULL,
    gate_id TEXT NOT NULL,
    gate_name TEXT NOT NULL,
    status TEXT NOT NULL,
    conditions TEXT NOT NULL,
    evidence_source TEXT NOT NULL,
    PRIMARY KEY (assurance_run_id, gate_id)
);

CREATE TABLE IF NOT EXISTS evidence_assurance_manifests (
    assurance_run_id TEXT NOT NULL,
    manifest_name TEXT NOT NULL,
    manifest_format TEXT NOT NULL,
    checksum TEXT NOT NULL,
    evidence_source TEXT NOT NULL,
    PRIMARY KEY (assurance_run_id, manifest_name)
);

CREATE INDEX IF NOT EXISTS idx_assurance_results_run
ON evidence_assurance_check_results(assurance_run_id);

CREATE INDEX IF NOT EXISTS idx_assurance_results_category
ON evidence_assurance_check_results(category);

CREATE INDEX IF NOT EXISTS idx_assurance_results_status
ON evidence_assurance_check_results(status);

CREATE INDEX IF NOT EXISTS idx_assurance_results_severity
ON evidence_assurance_check_results(severity);

CREATE INDEX IF NOT EXISTS idx_assurance_gates_status
ON evidence_assurance_release_gates(status);
