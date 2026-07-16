CREATE TABLE IF NOT EXISTS evidence_communication_runs (
    communication_run_id TEXT PRIMARY KEY,
    ingestion_run_id TEXT NOT NULL,
    quality_run_id TEXT NOT NULL,
    utilisation_run_id TEXT NOT NULL,
    forecast_run_id TEXT NOT NULL,
    scenario_run_id TEXT NOT NULL,
    optimisation_run_id TEXT NOT NULL,
    simulation_run_id TEXT NOT NULL,
    financial_run_id TEXT NOT NULL,
    framework_version TEXT NOT NULL,
    config_checksum TEXT NOT NULL,
    audience_catalogue_checksum TEXT NOT NULL,
    option_catalogue_checksum TEXT NOT NULL,
    challenge_catalogue_checksum TEXT NOT NULL,
    decision_status TEXT NOT NULL,
    approval_status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence_communication_audiences (
    communication_run_id TEXT NOT NULL,
    audience_id TEXT NOT NULL,
    label TEXT NOT NULL,
    detail_level TEXT NOT NULL,
    primary_need TEXT NOT NULL,
    PRIMARY KEY (communication_run_id, audience_id)
);

CREATE TABLE IF NOT EXISTS evidence_communication_options (
    communication_run_id TEXT NOT NULL,
    option_id TEXT NOT NULL,
    option_name TEXT NOT NULL,
    source_case_id TEXT NOT NULL,
    source_framework TEXT NOT NULL,
    feasibility_status TEXT NOT NULL,
    simulation_status TEXT NOT NULL,
    financial_readiness TEXT NOT NULL,
    nominal_npv REAL NOT NULL,
    risk_adjusted_npv REAL NOT NULL,
    payback_status TEXT NOT NULL,
    key_operational_risk TEXT NOT NULL,
    key_financial_risk TEXT NOT NULL,
    manual_review_required INTEGER NOT NULL,
    implementation_status TEXT NOT NULL,
    PRIMARY KEY (communication_run_id, option_id)
);

CREATE TABLE IF NOT EXISTS evidence_communication_products (
    communication_run_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    audience_id TEXT NOT NULL,
    file_name TEXT NOT NULL,
    product_type TEXT NOT NULL,
    checksum TEXT NOT NULL,
    PRIMARY KEY (communication_run_id, product_id)
);

CREATE TABLE IF NOT EXISTS evidence_communication_objections (
    communication_run_id TEXT NOT NULL,
    objection_id TEXT NOT NULL,
    stakeholder_group TEXT NOT NULL,
    objection_summary TEXT NOT NULL,
    evidence_required TEXT NOT NULL,
    source_evidence TEXT NOT NULL,
    status TEXT NOT NULL,
    analysis_response TEXT NOT NULL,
    decision_impact TEXT NOT NULL,
    revision_required INTEGER NOT NULL,
    scenario_label TEXT NOT NULL,
    PRIMARY KEY (communication_run_id, objection_id)
);

CREATE TABLE IF NOT EXISTS evidence_communication_challenges (
    communication_run_id TEXT NOT NULL,
    challenge_id TEXT NOT NULL,
    objection_id TEXT NOT NULL,
    support_status TEXT NOT NULL,
    evidence_considered TEXT NOT NULL,
    analytical_response TEXT NOT NULL,
    conclusion_change TEXT NOT NULL,
    unresolved_concern TEXT NOT NULL,
    PRIMARY KEY (communication_run_id, challenge_id)
);

CREATE TABLE IF NOT EXISTS evidence_communication_revisions (
    communication_run_id TEXT NOT NULL,
    revision_id TEXT NOT NULL,
    initial_position TEXT NOT NULL,
    challenge_id TEXT NOT NULL,
    evidence_considered TEXT NOT NULL,
    revised_position TEXT NOT NULL,
    reason_for_change TEXT NOT NULL,
    affected_outputs TEXT NOT NULL,
    status TEXT NOT NULL,
    PRIMARY KEY (communication_run_id, revision_id)
);

CREATE TABLE IF NOT EXISTS evidence_communication_claims (
    communication_run_id TEXT NOT NULL,
    claim_id TEXT NOT NULL,
    audience TEXT NOT NULL,
    claim_summary TEXT NOT NULL,
    source_table TEXT NOT NULL,
    source_run_id TEXT NOT NULL,
    source_record_or_metric TEXT NOT NULL,
    interpretation_rule TEXT NOT NULL,
    caveat TEXT NOT NULL,
    output_document TEXT NOT NULL,
    PRIMARY KEY (communication_run_id, claim_id)
);

CREATE TABLE IF NOT EXISTS evidence_communication_decision_records (
    communication_run_id TEXT NOT NULL,
    decision_record_id TEXT PRIMARY KEY,
    decision_context TEXT NOT NULL,
    evidence_lineage TEXT NOT NULL,
    options_considered TEXT NOT NULL,
    key_findings TEXT NOT NULL,
    assumptions TEXT NOT NULL,
    risks TEXT NOT NULL,
    uncertainties TEXT NOT NULL,
    challenges TEXT NOT NULL,
    revisions TEXT NOT NULL,
    conditions_precedent TEXT NOT NULL,
    decision_options TEXT NOT NULL,
    decision_status TEXT NOT NULL,
    approval_status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence_communication_provenance (
    communication_run_id TEXT NOT NULL,
    provenance_id TEXT NOT NULL,
    artefact_name TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_reference TEXT NOT NULL,
    checksum TEXT NOT NULL,
    PRIMARY KEY (communication_run_id, provenance_id)
);

CREATE INDEX IF NOT EXISTS idx_communication_runs_status
ON evidence_communication_runs(decision_status, approval_status);
CREATE INDEX IF NOT EXISTS idx_communication_audience
ON evidence_communication_audiences(communication_run_id, audience_id);
CREATE INDEX IF NOT EXISTS idx_communication_option
ON evidence_communication_options(communication_run_id, option_id);
CREATE INDEX IF NOT EXISTS idx_communication_objection
ON evidence_communication_objections(communication_run_id, objection_id);
CREATE INDEX IF NOT EXISTS idx_communication_claim
ON evidence_communication_claims(communication_run_id, claim_id);
