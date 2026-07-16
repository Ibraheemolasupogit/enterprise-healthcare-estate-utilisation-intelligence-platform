CREATE TABLE IF NOT EXISTS evidence_optimisation_runs (
    optimisation_run_id TEXT PRIMARY KEY,
    ingestion_run_id TEXT NOT NULL,
    quality_run_id TEXT NOT NULL,
    utilisation_run_id TEXT NOT NULL,
    forecast_run_id TEXT NOT NULL,
    scenario_run_id TEXT NOT NULL,
    framework_version TEXT NOT NULL,
    config_checksum TEXT NOT NULL,
    candidate_catalogue_checksum TEXT NOT NULL,
    constraint_catalogue_checksum TEXT NOT NULL,
    objective_catalogue_checksum TEXT NOT NULL,
    solver_identity TEXT NOT NULL,
    planning_demand_basis TEXT NOT NULL,
    readiness_status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence_optimisation_cases (
    optimisation_run_id TEXT NOT NULL,
    case_id TEXT NOT NULL,
    label TEXT NOT NULL,
    allow_room_deactivation INTEGER NOT NULL,
    allow_site_movement INTEGER NOT NULL,
    allow_remote_delivery INTEGER NOT NULL,
    PRIMARY KEY (optimisation_run_id, case_id)
);

CREATE TABLE IF NOT EXISTS evidence_optimisation_candidates (
    optimisation_run_id TEXT NOT NULL,
    candidate_id TEXT NOT NULL,
    service_id TEXT NOT NULL,
    source_site_id TEXT NOT NULL,
    target_site_id TEXT NOT NULL,
    target_building_id TEXT NOT NULL,
    target_room_id TEXT NOT NULL,
    period TEXT NOT NULL,
    planning_demand_hours REAL NOT NULL,
    compatible_capacity_hours REAL NOT NULL,
    room_type_compatible INTEGER NOT NULL,
    equipment_compatible INTEGER NOT NULL,
    capacity_compatible INTEGER NOT NULL,
    accessibility_compatible INTEGER NOT NULL,
    workforce_compatible INTEGER NOT NULL,
    co_location_compatible INTEGER NOT NULL,
    confidentiality_compatible INTEGER NOT NULL,
    protected_capacity_effect TEXT NOT NULL,
    travel_penalty REAL NOT NULL,
    relocation_penalty REAL NOT NULL,
    disruption_penalty REAL NOT NULL,
    candidate_status TEXT NOT NULL,
    exclusion_reason TEXT NOT NULL,
    PRIMARY KEY (optimisation_run_id, candidate_id)
);

CREATE TABLE IF NOT EXISTS evidence_optimisation_variables (
    optimisation_run_id TEXT NOT NULL,
    case_id TEXT NOT NULL,
    variable_id TEXT NOT NULL,
    variable_type TEXT NOT NULL,
    lower_bound REAL NOT NULL,
    upper_bound REAL,
    value REAL,
    PRIMARY KEY (optimisation_run_id, case_id, variable_id)
);

CREATE TABLE IF NOT EXISTS evidence_optimisation_allocations (
    optimisation_run_id TEXT NOT NULL,
    case_id TEXT NOT NULL,
    candidate_id TEXT NOT NULL,
    service_id TEXT NOT NULL,
    period TEXT NOT NULL,
    room_id TEXT NOT NULL,
    building_id TEXT NOT NULL,
    site_id TEXT NOT NULL,
    allocated_hours REAL NOT NULL,
    remote_hours REAL NOT NULL,
    unmet_demand_hours REAL NOT NULL,
    PRIMARY KEY (optimisation_run_id, case_id, candidate_id)
);

CREATE TABLE IF NOT EXISTS evidence_optimisation_room_status (
    optimisation_run_id TEXT NOT NULL,
    case_id TEXT NOT NULL,
    room_id TEXT NOT NULL,
    building_id TEXT NOT NULL,
    active_value REAL NOT NULL,
    protected_capacity_flag INTEGER NOT NULL,
    status TEXT NOT NULL,
    PRIMARY KEY (optimisation_run_id, case_id, room_id)
);

CREATE TABLE IF NOT EXISTS evidence_optimisation_building_status (
    optimisation_run_id TEXT NOT NULL,
    case_id TEXT NOT NULL,
    building_id TEXT NOT NULL,
    site_id TEXT NOT NULL,
    active_value REAL NOT NULL,
    potentially_releasable_flag INTEGER NOT NULL,
    status TEXT NOT NULL,
    PRIMARY KEY (optimisation_run_id, case_id, building_id)
);

CREATE TABLE IF NOT EXISTS evidence_optimisation_service_moves (
    optimisation_run_id TEXT NOT NULL,
    case_id TEXT NOT NULL,
    service_id TEXT NOT NULL,
    source_site_id TEXT NOT NULL,
    target_site_id TEXT NOT NULL,
    move_value REAL NOT NULL,
    moved_hours REAL NOT NULL,
    status TEXT NOT NULL,
    PRIMARY KEY (optimisation_run_id, case_id, service_id, source_site_id, target_site_id)
);

CREATE TABLE IF NOT EXISTS evidence_optimisation_constraints (
    optimisation_run_id TEXT NOT NULL,
    case_id TEXT NOT NULL,
    constraint_id TEXT NOT NULL,
    constraint_family TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    sense TEXT NOT NULL,
    rhs REAL NOT NULL,
    activity_value REAL NOT NULL,
    slack_value REAL NOT NULL,
    binding_flag INTEGER NOT NULL,
    result_status TEXT NOT NULL,
    PRIMARY KEY (optimisation_run_id, case_id, constraint_id)
);

CREATE TABLE IF NOT EXISTS evidence_optimisation_binding_constraints (
    optimisation_run_id TEXT NOT NULL,
    case_id TEXT NOT NULL,
    constraint_id TEXT NOT NULL,
    constraint_family TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    slack_value REAL NOT NULL,
    PRIMARY KEY (optimisation_run_id, case_id, constraint_id)
);

CREATE TABLE IF NOT EXISTS evidence_optimisation_objective_components (
    optimisation_run_id TEXT NOT NULL,
    case_id TEXT NOT NULL,
    component TEXT NOT NULL,
    component_value REAL NOT NULL,
    coefficient REAL NOT NULL,
    unit TEXT NOT NULL,
    PRIMARY KEY (optimisation_run_id, case_id, component)
);

CREATE TABLE IF NOT EXISTS evidence_optimisation_solver_results (
    optimisation_run_id TEXT NOT NULL,
    case_id TEXT NOT NULL,
    solver_name TEXT NOT NULL,
    solver_version TEXT NOT NULL,
    solver_status TEXT NOT NULL,
    mapped_status TEXT NOT NULL,
    objective_value REAL NOT NULL,
    objective_gap REAL NOT NULL,
    unmet_demand_hours REAL NOT NULL,
    allocated_demand_hours REAL NOT NULL,
    remote_demand_hours REAL NOT NULL,
    solve_diagnostics TEXT NOT NULL,
    PRIMARY KEY (optimisation_run_id, case_id)
);

CREATE TABLE IF NOT EXISTS evidence_optimisation_infeasibility (
    optimisation_run_id TEXT NOT NULL,
    case_id TEXT NOT NULL,
    diagnostic_id TEXT NOT NULL,
    diagnostic_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    shortfall_value REAL NOT NULL,
    detail TEXT NOT NULL,
    PRIMARY KEY (optimisation_run_id, case_id, diagnostic_id)
);

CREATE TABLE IF NOT EXISTS evidence_optimisation_comparison (
    optimisation_run_id TEXT NOT NULL,
    case_id TEXT NOT NULL,
    solver_status TEXT NOT NULL,
    objective_value REAL NOT NULL,
    planning_demand_hours REAL NOT NULL,
    allocated_demand_hours REAL NOT NULL,
    unmet_demand_hours REAL NOT NULL,
    active_rooms INTEGER NOT NULL,
    inactive_rooms INTEGER NOT NULL,
    active_buildings INTEGER NOT NULL,
    potentially_releasable_buildings INTEGER NOT NULL,
    services_moved INTEGER NOT NULL,
    remote_demand_hours REAL NOT NULL,
    comparison_statement TEXT NOT NULL,
    PRIMARY KEY (optimisation_run_id, case_id)
);

CREATE INDEX IF NOT EXISTS idx_optimisation_candidates_status
    ON evidence_optimisation_candidates (candidate_status, exclusion_reason);

CREATE INDEX IF NOT EXISTS idx_optimisation_allocations_case
    ON evidence_optimisation_allocations (case_id, service_id, period);

CREATE INDEX IF NOT EXISTS idx_optimisation_constraints_case
    ON evidence_optimisation_constraints (case_id, constraint_family, result_status);

CREATE INDEX IF NOT EXISTS idx_optimisation_comparison_status
    ON evidence_optimisation_comparison (solver_status, objective_value);
