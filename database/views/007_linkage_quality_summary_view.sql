CREATE VIEW IF NOT EXISTS linkage_quality_summary_view AS
SELECT
  entity_type,
  match_method,
  match_status,
  COUNT(*) AS record_count
FROM evidence_linkage_results
GROUP BY entity_type, match_method, match_status;

