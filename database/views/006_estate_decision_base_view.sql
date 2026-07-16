CREATE VIEW IF NOT EXISTS estate_decision_base_view AS
SELECT
  r.room_id,
  r.room_name,
  r.room_type,
  r.capacity,
  r.specialist_equipment,
  r.accessible_flag AS room_accessible_flag,
  r.protected_capacity_flag,
  b.building_id,
  b.building_name,
  b.site_id,
  b.building_type,
  b.ownership_type,
  b.floor_area_m2,
  b.accessibility_rating,
  b.condition_rating,
  b.ingestion_run_id
FROM curated_rooms r
LEFT JOIN curated_buildings b ON r.building_id = b.building_id;

