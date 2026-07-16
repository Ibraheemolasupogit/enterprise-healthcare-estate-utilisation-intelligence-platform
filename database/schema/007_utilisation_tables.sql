CREATE TABLE IF NOT EXISTS evidence_utilisation_runs (
  utilisation_run_id TEXT PRIMARY KEY,
  ingestion_run_id TEXT NOT NULL,
  quality_run_id TEXT NOT NULL,
  framework_version TEXT NOT NULL,
  config_checksum TEXT NOT NULL,
  formula_catalogue_checksum TEXT NOT NULL,
  overall_available_hours REAL NOT NULL,
  overall_booked_utilisation REAL NOT NULL,
  overall_actual_utilisation REAL NOT NULL,
  overall_effective_utilisation REAL NOT NULL,
  readiness_status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence_analytics_population (
  utilisation_run_id TEXT NOT NULL,
  dataset TEXT NOT NULL,
  record_identifier TEXT NOT NULL,
  record_status TEXT NOT NULL,
  analytical_status TEXT NOT NULL,
  quality_flag TEXT NOT NULL,
  PRIMARY KEY (utilisation_run_id, dataset, record_identifier)
);

CREATE TABLE IF NOT EXISTS evidence_analytics_exclusions (
  utilisation_run_id TEXT NOT NULL,
  dataset TEXT NOT NULL,
  record_identifier TEXT NOT NULL,
  rule_id TEXT,
  severity TEXT,
  failure_action TEXT,
  reason TEXT NOT NULL,
  analytical_effect TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence_room_utilisation (
  utilisation_run_id TEXT NOT NULL,
  room_id TEXT NOT NULL,
  building_id TEXT NOT NULL,
  site_id TEXT NOT NULL,
  available_hours REAL NOT NULL,
  booked_hours REAL NOT NULL,
  occupied_hours REAL NOT NULL,
  booked_utilisation REAL NOT NULL,
  actual_utilisation REAL NOT NULL,
  attendance_utilisation REAL NOT NULL,
  effective_utilisation REAL NOT NULL,
  completed_contacts INTEGER NOT NULL,
  protected_capacity_flag INTEGER NOT NULL,
  quality_flag TEXT NOT NULL,
  PRIMARY KEY (utilisation_run_id, room_id)
);

CREATE TABLE IF NOT EXISTS evidence_building_utilisation (
  utilisation_run_id TEXT NOT NULL,
  building_id TEXT NOT NULL,
  site_id TEXT NOT NULL,
  available_hours REAL NOT NULL,
  booked_hours REAL NOT NULL,
  occupied_hours REAL NOT NULL,
  booked_utilisation REAL NOT NULL,
  actual_utilisation REAL NOT NULL,
  effective_utilisation REAL NOT NULL,
  completed_contacts INTEGER NOT NULL,
  PRIMARY KEY (utilisation_run_id, building_id)
);

CREATE TABLE IF NOT EXISTS evidence_site_utilisation (
  utilisation_run_id TEXT NOT NULL,
  site_id TEXT NOT NULL,
  available_hours REAL NOT NULL,
  booked_hours REAL NOT NULL,
  occupied_hours REAL NOT NULL,
  booked_utilisation REAL NOT NULL,
  actual_utilisation REAL NOT NULL,
  effective_utilisation REAL NOT NULL,
  completed_contacts INTEGER NOT NULL,
  PRIMARY KEY (utilisation_run_id, site_id)
);

CREATE TABLE IF NOT EXISTS evidence_service_utilisation (
  utilisation_run_id TEXT NOT NULL,
  service_id TEXT NOT NULL,
  service_name TEXT NOT NULL,
  booked_hours REAL NOT NULL,
  occupied_hours REAL NOT NULL,
  planned_attendance INTEGER NOT NULL,
  actual_attendance INTEGER NOT NULL,
  completed_contacts INTEGER NOT NULL,
  attendance_utilisation REAL NOT NULL,
  cancellation_rate REAL NOT NULL,
  no_show_rate REAL NOT NULL,
  contacts_per_occupied_hour REAL NOT NULL,
  contacts_per_available_fte REAL NOT NULL,
  PRIMARY KEY (utilisation_run_id, service_id)
);

CREATE TABLE IF NOT EXISTS evidence_room_service_utilisation (
  utilisation_run_id TEXT NOT NULL,
  room_id TEXT NOT NULL,
  service_id TEXT NOT NULL,
  booked_hours REAL NOT NULL,
  occupied_hours REAL NOT NULL,
  completed_contacts INTEGER NOT NULL,
  PRIMARY KEY (utilisation_run_id, room_id, service_id)
);

CREATE TABLE IF NOT EXISTS evidence_time_band_utilisation (
  utilisation_run_id TEXT NOT NULL,
  grain TEXT NOT NULL,
  grain_value TEXT NOT NULL,
  booked_hours REAL NOT NULL,
  occupied_hours REAL NOT NULL,
  booking_count INTEGER NOT NULL,
  utilisation_value REAL NOT NULL,
  peak_flag INTEGER NOT NULL,
  PRIMARY KEY (utilisation_run_id, grain, grain_value)
);

CREATE TABLE IF NOT EXISTS evidence_monthly_utilisation (
  utilisation_run_id TEXT NOT NULL,
  month TEXT NOT NULL,
  room_id TEXT,
  available_hours REAL NOT NULL,
  booked_hours REAL NOT NULL,
  occupied_hours REAL NOT NULL,
  effective_utilisation REAL NOT NULL,
  observation_count INTEGER NOT NULL,
  PRIMARY KEY (utilisation_run_id, month, room_id)
);

CREATE TABLE IF NOT EXISTS evidence_underutilisation_flags (
  utilisation_run_id TEXT NOT NULL,
  room_id TEXT NOT NULL,
  effective_utilisation REAL NOT NULL,
  months_below_threshold INTEGER NOT NULL,
  observation_count INTEGER NOT NULL,
  persistent_flag INTEGER NOT NULL,
  protected_capacity_flag INTEGER NOT NULL,
  releasable_classification TEXT NOT NULL,
  exclusion_reason TEXT,
  PRIMARY KEY (utilisation_run_id, room_id)
);

CREATE TABLE IF NOT EXISTS evidence_unit_cost_metrics (
  utilisation_run_id TEXT NOT NULL,
  building_id TEXT NOT NULL,
  annual_operating_cost REAL NOT NULL,
  cost_per_available_room_hour REAL NOT NULL,
  cost_per_booked_room_hour REAL NOT NULL,
  cost_per_occupied_room_hour REAL NOT NULL,
  cost_per_completed_contact REAL NOT NULL,
  quality_flag TEXT NOT NULL,
  PRIMARY KEY (utilisation_run_id, building_id)
);

CREATE INDEX IF NOT EXISTS idx_utilisation_population_dataset
ON evidence_analytics_population(dataset, analytical_status);
CREATE INDEX IF NOT EXISTS idx_utilisation_exclusion_dataset
ON evidence_analytics_exclusions(dataset, record_identifier);
CREATE INDEX IF NOT EXISTS idx_utilisation_room_building
ON evidence_room_utilisation(building_id, site_id);
CREATE INDEX IF NOT EXISTS idx_utilisation_month_room
ON evidence_monthly_utilisation(room_id, month);
