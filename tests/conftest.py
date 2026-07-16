import sqlite3
from pathlib import Path

import pytest


@pytest.fixture()
def dashboard_database(tmp_path: Path) -> Path:
    """Create a minimal deterministic dashboard evidence database."""

    path = tmp_path / "dashboard.db"
    with sqlite3.connect(path) as connection:
        connection.executescript(
            """
            CREATE TABLE curated_sites (site_id TEXT);
            INSERT INTO curated_sites VALUES ('SITE-01');

            CREATE TABLE curated_buildings (
              site_id TEXT, building_id TEXT, building_name TEXT, ownership_type TEXT,
              building_type TEXT, floor_area_m2 REAL, condition_rating TEXT,
              accessibility_rating TEXT, active_flag TEXT, lease_start_date TEXT,
              lease_end_date TEXT
            );
            INSERT INTO curated_buildings VALUES (
              'SITE-01', 'BLD-01', 'North Wing', 'owned', 'clinical', 1000,
              'B', 'A', 'true', '2024-01-01', '2030-01-01'
            );

            CREATE TABLE curated_rooms (
              room_id TEXT, building_id TEXT, room_name TEXT, room_type TEXT, capacity INTEGER,
              specialist_equipment TEXT, accessible_flag TEXT, protected_capacity_flag TEXT
            );
            INSERT INTO curated_rooms VALUES (
              'ROOM-01', 'BLD-01', 'Consult 1', 'consult', 2, 'none', 'true', '1'
            );

            CREATE TABLE curated_services (service_id TEXT, service_name TEXT);
            INSERT INTO curated_services VALUES ('SVC-01', 'Community Care');

            CREATE TABLE curated_clinical_activity (activity_id TEXT);
            CREATE TABLE curated_workforce (
              record_date TEXT, service_id TEXT, site_id TEXT, staff_group TEXT,
              planned_fte REAL, available_fte REAL, absence_rate REAL, vacancy_rate REAL,
              remote_working_rate REAL, session_capacity REAL
            );
            CREATE TABLE curated_finance (finance_id TEXT);

            CREATE TABLE evidence_ingestion_runs (ingestion_run_id TEXT);
            INSERT INTO evidence_ingestion_runs VALUES ('ING-fixture');
            CREATE TABLE evidence_quality_runs (
              quality_run_id TEXT, overall_score REAL, overall_status TEXT
            );
            INSERT INTO evidence_quality_runs VALUES ('DQR-fixture', 91.0, 'pass_with_warnings');
            CREATE TABLE evidence_utilisation_runs (
              utilisation_run_id TEXT, overall_booked_utilisation REAL,
              overall_actual_utilisation REAL, overall_effective_utilisation REAL,
              readiness_status TEXT
            );
            INSERT INTO evidence_utilisation_runs VALUES (
              'UTL-fixture', 0.1, 0.1, 0.4, 'review_required'
            );
            CREATE TABLE evidence_forecast_runs (
              forecast_run_id TEXT, historical_start_period TEXT, historical_end_period TEXT,
              forecast_horizon INTEGER, readiness_status TEXT
            );
            INSERT INTO evidence_forecast_runs VALUES (
              'FCT-fixture', '2024-01', '2025-12', 6, 'forecast_ready'
            );
            CREATE TABLE evidence_scenario_runs (scenario_run_id TEXT);
            INSERT INTO evidence_scenario_runs VALUES ('SCN-fixture');
            CREATE TABLE evidence_optimisation_runs (optimisation_run_id TEXT);
            INSERT INTO evidence_optimisation_runs VALUES ('OPT-fixture');
            CREATE TABLE evidence_simulation_runs (
              simulation_run_id TEXT, readiness_status TEXT
            );
            INSERT INTO evidence_simulation_runs VALUES ('SIM-fixture', 'review_required');
            CREATE TABLE evidence_financial_runs (
              financial_run_id TEXT, readiness_status TEXT, analysis_horizon_years INTEGER
            );
            INSERT INTO evidence_financial_runs VALUES ('FIN-fixture', 'review_required', 5);

            CREATE TABLE evidence_room_utilisation (
              utilisation_run_id TEXT, room_id TEXT, site_id TEXT, building_id TEXT,
              protected_capacity_flag INTEGER, actual_utilisation REAL,
              effective_utilisation REAL
            );
            INSERT INTO evidence_room_utilisation VALUES (
              'UTL-fixture', 'ROOM-01', 'SITE-01', 'BLD-01', 1, 0.2, 0.5
            );
            CREATE TABLE evidence_building_utilisation (
              utilisation_run_id TEXT, building_id TEXT, actual_utilisation REAL,
              effective_utilisation REAL
            );
            INSERT INTO evidence_building_utilisation VALUES ('UTL-fixture', 'BLD-01', 0.2, 0.5);
            CREATE TABLE evidence_unit_cost_metrics (
              utilisation_run_id TEXT, building_id TEXT, annual_operating_cost REAL,
              cost_per_completed_contact REAL
            );
            INSERT INTO evidence_unit_cost_metrics VALUES ('UTL-fixture', 'BLD-01', 1000, 10);
            CREATE TABLE evidence_underutilisation_flags (
              utilisation_run_id TEXT, room_id TEXT, persistent_flag INTEGER,
              releasable_classification TEXT, months_below_threshold INTEGER
            );
            INSERT INTO evidence_underutilisation_flags VALUES (
              'UTL-fixture', 'ROOM-01', 1, 'review', 6
            );

            CREATE TABLE evidence_scenario_comparison (
              scenario_run_id TEXT, scenario_id TEXT
            );
            INSERT INTO evidence_scenario_comparison VALUES ('SCN-fixture', 'SCN-01');
            CREATE TABLE evidence_optimisation_cases (
              optimisation_run_id TEXT, case_id TEXT
            );
            INSERT INTO evidence_optimisation_cases VALUES ('OPT-fixture', 'CASE-01');
            CREATE TABLE evidence_quality_manual_review_queue (
              quality_run_id TEXT, status TEXT, severity TEXT, dataset TEXT
            );
            INSERT INTO evidence_quality_manual_review_queue VALUES (
              'DQR-fixture', 'open', 'medium', 'rooms'
            );
            CREATE TABLE evidence_financial_comparison (
              financial_run_id TEXT, financial_case_id TEXT, assumption_set TEXT,
              baseline_recurring_cost REAL, npv REAL, risk_adjusted_npv REAL
            );
            INSERT INTO evidence_financial_comparison VALUES (
              'FIN-fixture', 'FIN-01', 'base', 1000, 10, 0
            );
            CREATE TABLE evidence_financial_confidence (
              financial_run_id TEXT, financial_case_id TEXT, readiness_status TEXT
            );
            INSERT INTO evidence_financial_confidence VALUES (
              'FIN-fixture', 'FIN-01', 'not_realisable_without_mitigation'
            );
            CREATE TABLE evidence_simulation_workforce_metrics (
              simulation_run_id TEXT, simulation_case_id TEXT, experiment_id TEXT,
              service_id TEXT, workforce_utilisation REAL, blocked_demand_contacts REAL,
              workforce_bottleneck_count INTEGER
            );
            INSERT INTO evidence_simulation_workforce_metrics VALUES (
              'SIM-fixture', 'SIM-CASE-01', 'EXP-01', 'SVC-01', 1.2, 3, 1
            );
            """
        )
    return path
