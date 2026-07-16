CREATE TABLE IF NOT EXISTS evidence_scenario_runs (
    scenario_run_id TEXT PRIMARY KEY,
    ingestion_run_id TEXT NOT NULL,
    quality_run_id TEXT NOT NULL,
    utilisation_run_id TEXT NOT NULL,
    forecast_run_id TEXT NOT NULL,
    framework_version TEXT NOT NULL,
    config_checksum TEXT NOT NULL,
    scenario_catalogue_checksum TEXT NOT NULL,
    constraint_catalogue_checksum TEXT NOT NULL,
    demand_basis TEXT NOT NULL,
    interval_basis TEXT NOT NULL,
    readiness_status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence_scenario_catalogue (
    scenario_run_id TEXT NOT NULL,
    scenario_id TEXT NOT NULL,
    scenario_type TEXT NOT NULL,
    label TEXT NOT NULL,
    PRIMARY KEY (scenario_run_id, scenario_id)
);

CREATE TABLE IF NOT EXISTS evidence_scenario_candidates (
    scenario_run_id TEXT NOT NULL,
    scenario_id TEXT NOT NULL,
    candidate_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    rank_value REAL NOT NULL,
    selected_flag INTEGER NOT NULL,
    reason TEXT NOT NULL,
    PRIMARY KEY (scenario_run_id, scenario_id, candidate_type, entity_id)
);

CREATE TABLE IF NOT EXISTS evidence_scenario_room_actions (
    scenario_run_id TEXT NOT NULL,
    scenario_id TEXT NOT NULL,
    room_id TEXT NOT NULL,
    building_id TEXT NOT NULL,
    action TEXT NOT NULL,
    reason TEXT NOT NULL,
    protected_capacity_flag INTEGER NOT NULL,
    specialist_flag INTEGER NOT NULL,
    PRIMARY KEY (scenario_run_id, scenario_id, room_id)
);

CREATE TABLE IF NOT EXISTS evidence_scenario_service_moves (
    scenario_run_id TEXT NOT NULL,
    scenario_id TEXT NOT NULL,
    service_id TEXT NOT NULL,
    from_site_id TEXT NOT NULL,
    to_site_id TEXT NOT NULL,
    planning_demand_room_hours REAL NOT NULL,
    status TEXT NOT NULL,
    reason TEXT NOT NULL,
    PRIMARY KEY (scenario_run_id, scenario_id, service_id, from_site_id, to_site_id)
);

CREATE TABLE IF NOT EXISTS evidence_scenario_capacity (
    scenario_run_id TEXT NOT NULL,
    scenario_id TEXT NOT NULL,
    grain TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    point_demand_room_hours REAL NOT NULL,
    interval_demand_room_hours REAL NOT NULL,
    planning_demand_room_hours REAL NOT NULL,
    available_room_hours REAL NOT NULL,
    compatible_available_room_hours REAL NOT NULL,
    capacity_headroom REAL NOT NULL,
    contingency_headroom REAL NOT NULL,
    capacity_shortfall REAL NOT NULL,
    utilisation_after_scenario REAL NOT NULL,
    rooms_retained INTEGER NOT NULL,
    rooms_deactivated INTEGER NOT NULL,
    protected_rooms_retained INTEGER NOT NULL,
    specialist_rooms_retained INTEGER NOT NULL,
    unallocated_demand REAL NOT NULL,
    PRIMARY KEY (scenario_run_id, scenario_id, grain, entity_id)
);

CREATE TABLE IF NOT EXISTS evidence_scenario_compatibility (
    scenario_run_id TEXT NOT NULL,
    scenario_id TEXT NOT NULL,
    service_id TEXT NOT NULL,
    room_id TEXT NOT NULL,
    compatibility_status TEXT NOT NULL,
    reason TEXT NOT NULL,
    PRIMARY KEY (scenario_run_id, scenario_id, service_id, room_id)
);

CREATE TABLE IF NOT EXISTS evidence_scenario_workforce (
    scenario_run_id TEXT NOT NULL,
    scenario_id TEXT NOT NULL,
    service_id TEXT NOT NULL,
    site_id TEXT NOT NULL,
    available_fte REAL NOT NULL,
    planned_fte REAL NOT NULL,
    availability_ratio REAL NOT NULL,
    status TEXT NOT NULL,
    warning TEXT,
    PRIMARY KEY (scenario_run_id, scenario_id, service_id, site_id)
);

CREATE TABLE IF NOT EXISTS evidence_scenario_accessibility (
    scenario_run_id TEXT NOT NULL,
    scenario_id TEXT NOT NULL,
    site_id TEXT NOT NULL,
    origin_areas INTEGER NOT NULL,
    average_distance_km REAL NOT NULL,
    maximum_distance_km REAL NOT NULL,
    average_travel_minutes REAL NOT NULL,
    average_public_transport_score REAL NOT NULL,
    accessible_transport_coverage REAL NOT NULL,
    accessibility_status TEXT NOT NULL,
    warning TEXT,
    PRIMARY KEY (scenario_run_id, scenario_id, site_id)
);

CREATE TABLE IF NOT EXISTS evidence_scenario_costs (
    scenario_run_id TEXT NOT NULL,
    scenario_id TEXT NOT NULL,
    baseline_recurring_cost REAL NOT NULL,
    scenario_recurring_cost REAL NOT NULL,
    descriptive_recurring_cost_difference REAL NOT NULL,
    indicative_transition_cost_exposure REAL NOT NULL,
    planned_capital_cost_exposure REAL NOT NULL,
    exit_cost_exposure REAL NOT NULL,
    relocation_cost_exposure REAL NOT NULL,
    cost_statement TEXT NOT NULL,
    PRIMARY KEY (scenario_run_id, scenario_id)
);

CREATE TABLE IF NOT EXISTS evidence_scenario_constraints (
    scenario_run_id TEXT NOT NULL,
    scenario_id TEXT NOT NULL,
    constraint_category TEXT NOT NULL,
    constraint_name TEXT NOT NULL,
    result_status TEXT NOT NULL,
    critical_flag INTEGER NOT NULL,
    detail TEXT NOT NULL,
    PRIMARY KEY (scenario_run_id, scenario_id, constraint_category, constraint_name)
);

CREATE TABLE IF NOT EXISTS evidence_scenario_risks (
    scenario_run_id TEXT NOT NULL,
    scenario_id TEXT NOT NULL,
    risk_category TEXT NOT NULL,
    risk_level TEXT NOT NULL,
    confidence_status TEXT NOT NULL,
    detail TEXT NOT NULL,
    PRIMARY KEY (scenario_run_id, scenario_id, risk_category)
);

CREATE TABLE IF NOT EXISTS evidence_scenario_scores (
    scenario_run_id TEXT NOT NULL,
    scenario_id TEXT NOT NULL,
    dimension TEXT NOT NULL,
    raw_value REAL NOT NULL,
    weight REAL NOT NULL,
    weighted_score REAL NOT NULL,
    PRIMARY KEY (scenario_run_id, scenario_id, dimension)
);

CREATE TABLE IF NOT EXISTS evidence_scenario_comparison (
    scenario_run_id TEXT NOT NULL,
    scenario_id TEXT NOT NULL,
    feasibility_status TEXT NOT NULL,
    comparison_score REAL NOT NULL,
    confidence_status TEXT NOT NULL,
    rooms_retained INTEGER NOT NULL,
    rooms_deactivated INTEGER NOT NULL,
    buildings_affected INTEGER NOT NULL,
    services_moved INTEGER NOT NULL,
    planning_demand_room_hours REAL NOT NULL,
    compatible_capacity_room_hours REAL NOT NULL,
    capacity_headroom REAL NOT NULL,
    unallocated_demand REAL NOT NULL,
    protected_capacity_retained INTEGER NOT NULL,
    comparison_statement TEXT NOT NULL,
    PRIMARY KEY (scenario_run_id, scenario_id)
);

CREATE INDEX IF NOT EXISTS idx_scenario_comparison_status
    ON evidence_scenario_comparison (scenario_run_id, feasibility_status);
CREATE INDEX IF NOT EXISTS idx_scenario_capacity_entity
    ON evidence_scenario_capacity (scenario_run_id, scenario_id, grain, entity_id);
CREATE INDEX IF NOT EXISTS idx_scenario_constraints_status
    ON evidence_scenario_constraints (scenario_run_id, scenario_id, result_status);
