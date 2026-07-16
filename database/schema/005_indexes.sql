CREATE INDEX IF NOT EXISTS idx_linkage_entity ON evidence_linkage_results(entity_type);
CREATE INDEX IF NOT EXISTS idx_linkage_status ON evidence_linkage_results(match_status);
CREATE INDEX IF NOT EXISTS idx_reconciliation_run ON evidence_reconciliation_summary(ingestion_run_id);
CREATE INDEX IF NOT EXISTS idx_duplicate_dataset ON evidence_duplicate_candidates(dataset);
CREATE INDEX IF NOT EXISTS idx_unmatched_dataset ON evidence_unmatched_records(dataset);

