CREATE VIEW IF NOT EXISTS curated_activity_context_view AS
SELECT
  a.activity_id,
  a.service_id,
  s.service_name,
  a.room_id,
  r.building_id,
  bd.site_id,
  a.activity_date,
  a.appointment_type,
  a.scheduled_contacts,
  a.completed_contacts,
  a.face_to_face_contacts,
  a.remote_contacts,
  a.did_not_attend_count,
  a.cancelled_contacts,
  a.record_status,
  a.warning_reason,
  a.ingestion_run_id
FROM curated_clinical_activity a
LEFT JOIN curated_services s ON a.service_id = s.service_id
LEFT JOIN curated_rooms r ON a.room_id = r.room_id
LEFT JOIN curated_buildings bd ON r.building_id = bd.building_id;

