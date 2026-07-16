CREATE TABLE IF NOT EXISTS evidence_quality_runs (
  quality_run_id TEXT PRIMARY KEY,
  ingestion_run_id TEXT NOT NULL,
  framework_version TEXT NOT NULL,
  config_checksum TEXT NOT NULL,
  rule_catalogue_checksum TEXT NOT NULL,
  overall_score REAL NOT NULL,
  overall_status TEXT NOT NULL,
  reference_date TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence_quality_rule_catalogue (
  rule_id TEXT PRIMARY KEY,
  rule_name TEXT NOT NULL,
  dataset TEXT NOT NULL,
  dimension TEXT NOT NULL,
  description TEXT NOT NULL,
  severity TEXT NOT NULL,
  field_names TEXT NOT NULL,
  scope TEXT NOT NULL,
  threshold TEXT NOT NULL,
  enabled INTEGER NOT NULL,
  expected_outcome TEXT NOT NULL,
  failure_action TEXT NOT NULL,
  downstream_impact TEXT NOT NULL,
  milestone_owner TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence_quality_check_results (
  evidence_key TEXT PRIMARY KEY,
  quality_run_id TEXT NOT NULL,
  rule_id TEXT NOT NULL,
  dataset TEXT NOT NULL,
  dimension TEXT NOT NULL,
  severity TEXT NOT NULL,
  status TEXT NOT NULL,
  records_checked INTEGER NOT NULL,
  records_failed INTEGER NOT NULL,
  failure_action TEXT NOT NULL,
  message TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence_quality_record_issues (
  evidence_key TEXT PRIMARY KEY,
  quality_run_id TEXT NOT NULL,
  rule_id TEXT NOT NULL,
  dataset TEXT NOT NULL,
  record_identifier TEXT NOT NULL,
  field_name TEXT NOT NULL,
  observed_value TEXT,
  expected_condition TEXT NOT NULL,
  severity TEXT NOT NULL,
  failure_action TEXT NOT NULL,
  status TEXT NOT NULL,
  issue_description TEXT NOT NULL,
  source_file TEXT,
  source_row_number INTEGER,
  intentional_issue_id TEXT
);

CREATE TABLE IF NOT EXISTS evidence_quality_dataset_scores (
  quality_run_id TEXT NOT NULL,
  dataset TEXT NOT NULL,
  score REAL NOT NULL,
  status TEXT NOT NULL,
  passed_checks INTEGER NOT NULL,
  failed_checks INTEGER NOT NULL,
  PRIMARY KEY (quality_run_id, dataset)
);

CREATE TABLE IF NOT EXISTS evidence_quality_dimension_scores (
  quality_run_id TEXT NOT NULL,
  dataset TEXT NOT NULL,
  dimension TEXT NOT NULL,
  score REAL NOT NULL,
  status TEXT NOT NULL,
  applicable_checks INTEGER NOT NULL,
  failed_checks INTEGER NOT NULL,
  PRIMARY KEY (quality_run_id, dataset, dimension)
);

CREATE TABLE IF NOT EXISTS evidence_quality_reconciliation_results (
  evidence_key TEXT PRIMARY KEY,
  quality_run_id TEXT NOT NULL,
  reconciliation_name TEXT NOT NULL,
  dataset TEXT NOT NULL,
  status TEXT NOT NULL,
  expected_value TEXT NOT NULL,
  observed_value TEXT NOT NULL,
  tolerance TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence_quality_manual_review_queue (
  review_id TEXT PRIMARY KEY,
  quality_run_id TEXT NOT NULL,
  dataset TEXT NOT NULL,
  record_identifier TEXT NOT NULL,
  rule_id TEXT NOT NULL,
  issue_summary TEXT NOT NULL,
  severity TEXT NOT NULL,
  source_file TEXT,
  source_row_number INTEGER,
  recommended_review_action TEXT NOT NULL,
  status TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_quality_result_run ON evidence_quality_check_results(quality_run_id);
CREATE INDEX IF NOT EXISTS idx_quality_issue_dataset ON evidence_quality_record_issues(dataset);
CREATE INDEX IF NOT EXISTS idx_quality_manual_status ON evidence_quality_manual_review_queue(status);

