CREATE VIEW IF NOT EXISTS curated_booking_context_view AS
SELECT
  b.booking_id,
  b.room_id,
  r.building_id,
  r.room_name,
  bd.site_id,
  b.service_id,
  s.service_name,
  b.booking_date,
  b.start_time,
  b.end_time,
  b.booking_status,
  b.cancellation_flag,
  b.no_show_flag,
  b.actual_attendance_count,
  b.planned_attendance_count,
  b.record_status,
  b.warning_reason,
  b.ingestion_run_id
FROM curated_bookings b
LEFT JOIN curated_rooms r ON b.room_id = r.room_id
LEFT JOIN curated_buildings bd ON r.building_id = bd.building_id
LEFT JOIN curated_services s ON b.service_id = s.service_id;

