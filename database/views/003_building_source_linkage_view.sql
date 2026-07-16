CREATE VIEW IF NOT EXISTS building_source_linkage_view AS
SELECT
  building_id,
  site_id,
  building_name,
  building_type,
  ownership_type,
  floor_area_m2,
  accessibility_rating,
  condition_rating,
  record_status,
  warning_reason,
  ingestion_run_id
FROM curated_buildings;

