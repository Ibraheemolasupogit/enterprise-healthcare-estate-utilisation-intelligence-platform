CREATE VIEW IF NOT EXISTS room_source_linkage_view AS
SELECT
  room_id,
  building_id,
  room_name,
  room_type,
  capacity,
  specialist_equipment,
  accessible_flag,
  protected_capacity_flag,
  record_status,
  warning_reason,
  ingestion_run_id
FROM curated_rooms;

