CREATE VIEW IF NOT EXISTS service_source_linkage_view AS
SELECT
  service_id,
  service_name,
  clinical_specialty,
  minimum_room_type,
  specialist_equipment_required,
  confidentiality_requirement,
  record_status,
  warning_reason,
  ingestion_run_id
FROM curated_services;

