CREATE TABLE IF NOT EXISTS evidence_ingestion_runs (
  ingestion_run_id TEXT PRIMARY KEY,
  generator_version TEXT NOT NULL,
  project_version TEXT NOT NULL,
  master_seed TEXT NOT NULL,
  reference_date TEXT NOT NULL,
  contract_version TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence_source_files (
  ingestion_run_id TEXT NOT NULL,
  dataset TEXT NOT NULL,
  file_name TEXT NOT NULL,
  checksum TEXT NOT NULL,
  checksum_verified INTEGER NOT NULL,
  PRIMARY KEY (ingestion_run_id, dataset)
);

CREATE TABLE IF NOT EXISTS evidence_linkage_results (
  linkage_id TEXT PRIMARY KEY,
  entity_type TEXT NOT NULL,
  source_dataset TEXT NOT NULL,
  source_record_identifier TEXT NOT NULL,
  source_value TEXT NOT NULL,
  canonical_entity_id TEXT,
  match_method TEXT NOT NULL,
  match_score REAL NOT NULL,
  match_status TEXT NOT NULL,
  parent_context TEXT NOT NULL,
  normalised_value TEXT NOT NULL,
  reason TEXT NOT NULL,
  ingestion_run_id TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence_unmatched_records (
  dataset TEXT NOT NULL,
  record_identifier TEXT NOT NULL,
  field TEXT NOT NULL,
  source_value TEXT,
  reason TEXT NOT NULL,
  ingestion_run_id TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence_duplicate_candidates (
  duplicate_group_id TEXT PRIMARY KEY,
  dataset TEXT NOT NULL,
  record_identifiers TEXT NOT NULL,
  duplicate_type TEXT NOT NULL,
  match_basis TEXT NOT NULL,
  severity TEXT NOT NULL,
  recommended_action TEXT NOT NULL,
  ingestion_run_id TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence_reconciliation_summary (
  dataset TEXT PRIMARY KEY,
  source_rows INTEGER NOT NULL,
  staging_rows INTEGER NOT NULL,
  curated_rows INTEGER NOT NULL,
  accepted_rows INTEGER NOT NULL,
  warning_rows INTEGER NOT NULL,
  rejected_rows INTEGER NOT NULL,
  duplicate_candidates INTEGER NOT NULL,
  unmatched_references INTEGER NOT NULL,
  checksum_verified INTEGER NOT NULL,
  ingestion_run_id TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence_intentional_issue_detection (
  issue_id TEXT PRIMARY KEY,
  dataset TEXT NOT NULL,
  record_identifier TEXT NOT NULL,
  issue_type TEXT NOT NULL,
  expected_detection_milestone INTEGER NOT NULL,
  detected INTEGER NOT NULL,
  intentional INTEGER NOT NULL,
  ingestion_run_id TEXT NOT NULL
);

