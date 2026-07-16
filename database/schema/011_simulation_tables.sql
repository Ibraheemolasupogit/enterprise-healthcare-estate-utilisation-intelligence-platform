CREATE TABLE IF NOT EXISTS evidence_simulation_runs (
    simulation_run_id TEXT PRIMARY KEY,
    ingestion_run_id TEXT NOT NULL,
    quality_run_id TEXT NOT NULL,
    utilisation_run_id TEXT NOT NULL,
    forecast_run_id TEXT NOT NULL,
    scenario_run_id TEXT NOT NULL,
    optimisation_run_id TEXT NOT NULL,
    framework_version TEXT NOT NULL,
    config_checksum TEXT NOT NULL,
    experiment_catalogue_checksum TEXT NOT NULL,
    allocation_catalogue_checksum TEXT NOT NULL,
    seed_strategy_version TEXT NOT NULL,
    simulation_engine_identity TEXT NOT NULL,
    master_seed INTEGER NOT NULL,
    replications INTEGER NOT NULL,
    simulation_horizon INTEGER NOT NULL,
    time_unit TEXT NOT NULL,
    readiness_status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence_simulation_cases (
    simulation_run_id TEXT NOT NULL,
    simulation_case_id TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_case_id TEXT NOT NULL,
    label TEXT NOT NULL,
    active_rooms INTEGER NOT NULL,
    allocated_service_rooms INTEGER NOT NULL,
    PRIMARY KEY (simulation_run_id, simulation_case_id)
);

CREATE TABLE IF NOT EXISTS evidence_simulation_experiments (
    simulation_run_id TEXT NOT NULL,
    experiment_id TEXT NOT NULL,
    label TEXT NOT NULL,
    demand_multiplier REAL NOT NULL,
    workforce_multiplier REAL NOT NULL,
    duration_multiplier REAL NOT NULL,
    specialist_room_capacity_multiplier REAL NOT NULL,
    PRIMARY KEY (simulation_run_id, experiment_id)
);

CREATE TABLE IF NOT EXISTS evidence_simulation_replications (
    simulation_run_id TEXT NOT NULL,
    simulation_case_id TEXT NOT NULL,
    experiment_id TEXT NOT NULL,
    replication INTEGER NOT NULL,
    replication_seed INTEGER NOT NULL,
    arrivals INTEGER NOT NULL,
    completed_contacts INTEGER NOT NULL,
    unserved_contacts INTEGER NOT NULL,
    completion_rate REAL NOT NULL,
    mean_wait_minutes REAL NOT NULL,
    p95_wait_minutes REAL NOT NULL,
    room_contention_events INTEGER NOT NULL,
    workforce_blocked_contacts INTEGER NOT NULL,
    status TEXT NOT NULL,
    PRIMARY KEY (simulation_run_id, simulation_case_id, experiment_id, replication)
);

CREATE TABLE IF NOT EXISTS evidence_simulation_events (
    simulation_run_id TEXT NOT NULL,
    simulation_case_id TEXT NOT NULL,
    experiment_id TEXT NOT NULL,
    replication INTEGER NOT NULL,
    event_sequence INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    event_time REAL NOT NULL,
    service_id TEXT NOT NULL,
    room_id TEXT NOT NULL,
    wait_minutes REAL NOT NULL,
    service_duration_minutes REAL NOT NULL,
    completion_status TEXT NOT NULL,
    PRIMARY KEY (
        simulation_run_id, simulation_case_id, experiment_id, replication, event_sequence
    )
);

CREATE TABLE IF NOT EXISTS evidence_simulation_resource_metrics (
    simulation_run_id TEXT NOT NULL,
    simulation_case_id TEXT NOT NULL,
    experiment_id TEXT NOT NULL,
    room_id TEXT NOT NULL,
    building_id TEXT NOT NULL,
    site_id TEXT NOT NULL,
    room_type TEXT NOT NULL,
    protected_capacity_flag INTEGER NOT NULL,
    specialist_flag INTEGER NOT NULL,
    busy_minutes REAL NOT NULL,
    idle_minutes REAL NOT NULL,
    occupancy_rate REAL NOT NULL,
    overtime_minutes REAL NOT NULL,
    contention_events INTEGER NOT NULL,
    peak_queue_length INTEGER NOT NULL,
    capacity_breaches INTEGER NOT NULL,
    PRIMARY KEY (simulation_run_id, simulation_case_id, experiment_id, room_id)
);

CREATE TABLE IF NOT EXISTS evidence_simulation_service_metrics (
    simulation_run_id TEXT NOT NULL,
    simulation_case_id TEXT NOT NULL,
    experiment_id TEXT NOT NULL,
    service_id TEXT NOT NULL,
    arrivals INTEGER NOT NULL,
    completed_contacts INTEGER NOT NULL,
    unserved_contacts INTEGER NOT NULL,
    completion_rate REAL NOT NULL,
    mean_wait_minutes REAL NOT NULL,
    median_wait_minutes REAL NOT NULL,
    p90_wait_minutes REAL NOT NULL,
    p95_wait_minutes REAL NOT NULL,
    max_wait_minutes REAL NOT NULL,
    delayed_session_count INTEGER NOT NULL,
    threshold_exceedance_rate REAL NOT NULL,
    session_overrun_minutes REAL NOT NULL,
    unmet_simulated_demand INTEGER NOT NULL,
    status TEXT NOT NULL,
    PRIMARY KEY (simulation_run_id, simulation_case_id, experiment_id, service_id)
);

CREATE TABLE IF NOT EXISTS evidence_simulation_queue_metrics (
    simulation_run_id TEXT NOT NULL,
    simulation_case_id TEXT NOT NULL,
    experiment_id TEXT NOT NULL,
    service_id TEXT NOT NULL,
    room_id TEXT NOT NULL,
    mean_queue_length REAL NOT NULL,
    peak_queue_length INTEGER NOT NULL,
    contention_events INTEGER NOT NULL,
    mean_wait_minutes REAL NOT NULL,
    p95_wait_minutes REAL NOT NULL,
    PRIMARY KEY (simulation_run_id, simulation_case_id, experiment_id, service_id, room_id)
);

CREATE TABLE IF NOT EXISTS evidence_simulation_workforce_metrics (
    simulation_run_id TEXT NOT NULL,
    simulation_case_id TEXT NOT NULL,
    experiment_id TEXT NOT NULL,
    service_id TEXT NOT NULL,
    available_contact_slots REAL NOT NULL,
    used_contact_slots REAL NOT NULL,
    workforce_utilisation REAL NOT NULL,
    blocked_demand_contacts INTEGER NOT NULL,
    overtime_minutes REAL NOT NULL,
    workforce_bottleneck_count INTEGER NOT NULL,
    PRIMARY KEY (simulation_run_id, simulation_case_id, experiment_id, service_id)
);

CREATE TABLE IF NOT EXISTS evidence_simulation_resilience_metrics (
    simulation_run_id TEXT NOT NULL,
    simulation_case_id TEXT NOT NULL,
    experiment_id TEXT NOT NULL,
    arrivals INTEGER NOT NULL,
    completed_contacts INTEGER NOT NULL,
    completion_rate REAL NOT NULL,
    mean_wait_minutes REAL NOT NULL,
    p95_wait_minutes REAL NOT NULL,
    max_wait_minutes REAL NOT NULL,
    room_occupancy REAL NOT NULL,
    overtime_minutes REAL NOT NULL,
    unserved_contacts INTEGER NOT NULL,
    contingency_consumed REAL NOT NULL,
    contingency_remaining REAL NOT NULL,
    threshold_failure_frequency REAL NOT NULL,
    ci_method TEXT NOT NULL,
    ci_level REAL NOT NULL,
    completion_rate_ci_low REAL NOT NULL,
    completion_rate_ci_high REAL NOT NULL,
    mean_wait_ci_low REAL NOT NULL,
    mean_wait_ci_high REAL NOT NULL,
    status TEXT NOT NULL,
    PRIMARY KEY (simulation_run_id, simulation_case_id, experiment_id)
);

CREATE TABLE IF NOT EXISTS evidence_simulation_threshold_results (
    simulation_run_id TEXT NOT NULL,
    simulation_case_id TEXT NOT NULL,
    experiment_id TEXT NOT NULL,
    threshold_name TEXT NOT NULL,
    threshold_value REAL NOT NULL,
    observed_value REAL NOT NULL,
    result_status TEXT NOT NULL,
    PRIMARY KEY (simulation_run_id, simulation_case_id, experiment_id, threshold_name)
);

CREATE TABLE IF NOT EXISTS evidence_simulation_summary (
    simulation_run_id TEXT NOT NULL,
    simulation_case_id TEXT NOT NULL,
    experiment_id TEXT NOT NULL,
    status TEXT NOT NULL,
    arrivals INTEGER NOT NULL,
    completed_contacts INTEGER NOT NULL,
    unserved_contacts INTEGER NOT NULL,
    completion_rate REAL NOT NULL,
    mean_wait_minutes REAL NOT NULL,
    p95_wait_minutes REAL NOT NULL,
    room_occupancy REAL NOT NULL,
    overtime_minutes REAL NOT NULL,
    workforce_bottleneck_count INTEGER NOT NULL,
    comparison_statement TEXT NOT NULL,
    PRIMARY KEY (simulation_run_id, simulation_case_id, experiment_id)
);

CREATE TABLE IF NOT EXISTS evidence_simulation_failures (
    simulation_run_id TEXT NOT NULL,
    simulation_case_id TEXT NOT NULL,
    experiment_id TEXT NOT NULL,
    failure_id TEXT NOT NULL,
    failure_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    observed_value REAL NOT NULL,
    threshold_value REAL NOT NULL,
    detail TEXT NOT NULL,
    PRIMARY KEY (simulation_run_id, simulation_case_id, experiment_id, failure_id)
);

CREATE INDEX IF NOT EXISTS idx_sim_cases_run ON evidence_simulation_cases(simulation_run_id);
CREATE INDEX IF NOT EXISTS idx_sim_replications_case_exp
    ON evidence_simulation_replications(simulation_case_id, experiment_id);
CREATE INDEX IF NOT EXISTS idx_sim_resource_case_exp
    ON evidence_simulation_resource_metrics(simulation_case_id, experiment_id);
CREATE INDEX IF NOT EXISTS idx_sim_service_case_exp
    ON evidence_simulation_service_metrics(simulation_case_id, experiment_id, service_id);
CREATE INDEX IF NOT EXISTS idx_sim_threshold_case_exp
    ON evidence_simulation_threshold_results(simulation_case_id, experiment_id);
