CREATE TABLE IF NOT EXISTS evidence_financial_runs (
    financial_run_id TEXT PRIMARY KEY,
    ingestion_run_id TEXT NOT NULL,
    quality_run_id TEXT NOT NULL,
    utilisation_run_id TEXT NOT NULL,
    forecast_run_id TEXT NOT NULL,
    scenario_run_id TEXT NOT NULL,
    optimisation_run_id TEXT NOT NULL,
    simulation_run_id TEXT NOT NULL,
    framework_version TEXT NOT NULL,
    config_checksum TEXT NOT NULL,
    financial_case_catalogue_checksum TEXT NOT NULL,
    assumption_catalogue_checksum TEXT NOT NULL,
    formula_catalogue_checksum TEXT NOT NULL,
    currency TEXT NOT NULL,
    price_basis TEXT NOT NULL,
    analysis_horizon_years INTEGER NOT NULL,
    discount_rate REAL NOT NULL,
    annual_cost_escalation REAL NOT NULL,
    readiness_status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence_financial_case_catalogue (
    financial_run_id TEXT NOT NULL,
    financial_case_id TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_case_id TEXT NOT NULL,
    simulation_case_id TEXT NOT NULL,
    label TEXT NOT NULL,
    PRIMARY KEY (financial_run_id, financial_case_id)
);

CREATE TABLE IF NOT EXISTS evidence_financial_assumptions (
    financial_run_id TEXT NOT NULL,
    assumption_set TEXT NOT NULL,
    assumption_name TEXT NOT NULL,
    assumption_value TEXT NOT NULL,
    evidence_source TEXT NOT NULL,
    PRIMARY KEY (financial_run_id, assumption_set, assumption_name)
);

CREATE TABLE IF NOT EXISTS evidence_financial_recurring_costs (
    financial_run_id TEXT NOT NULL,
    financial_case_id TEXT NOT NULL,
    cost_component TEXT NOT NULL,
    baseline_amount REAL NOT NULL,
    case_amount REAL NOT NULL,
    gross_recurring_cost_difference REAL NOT NULL,
    classification TEXT NOT NULL,
    release_treatment TEXT NOT NULL,
    evidence_source TEXT NOT NULL,
    PRIMARY KEY (financial_run_id, financial_case_id, cost_component)
);

CREATE TABLE IF NOT EXISTS evidence_financial_transition_costs (
    financial_run_id TEXT NOT NULL,
    financial_case_id TEXT NOT NULL,
    cost_component TEXT NOT NULL,
    amount REAL NOT NULL,
    timing_year INTEGER NOT NULL,
    trigger TEXT NOT NULL,
    formula TEXT NOT NULL,
    coefficient REAL NOT NULL,
    uncertainty_low REAL NOT NULL,
    uncertainty_high REAL NOT NULL,
    evidence_source TEXT NOT NULL,
    inclusion_reason TEXT NOT NULL,
    PRIMARY KEY (financial_run_id, financial_case_id, cost_component)
);

CREATE TABLE IF NOT EXISTS evidence_financial_mitigation_costs (
    financial_run_id TEXT NOT NULL,
    financial_case_id TEXT NOT NULL,
    cost_component TEXT NOT NULL,
    annual_amount REAL NOT NULL,
    trigger TEXT NOT NULL,
    linked_failure_count INTEGER NOT NULL,
    evidence_source TEXT NOT NULL,
    inclusion_reason TEXT NOT NULL,
    PRIMARY KEY (financial_run_id, financial_case_id, cost_component)
);

CREATE TABLE IF NOT EXISTS evidence_financial_cashflows (
    financial_run_id TEXT NOT NULL,
    financial_case_id TEXT NOT NULL,
    assumption_set TEXT NOT NULL,
    analysis_year INTEGER NOT NULL,
    baseline_recurring_cost REAL NOT NULL,
    case_recurring_cost REAL NOT NULL,
    gross_recurring_difference REAL NOT NULL,
    transition_costs REAL NOT NULL,
    mitigation_costs REAL NOT NULL,
    implementation_costs REAL NOT NULL,
    net_annual_financial_effect REAL NOT NULL,
    discount_factor REAL NOT NULL,
    discounted_cash_flow REAL NOT NULL,
    cumulative_cash_flow REAL NOT NULL,
    PRIMARY KEY (financial_run_id, financial_case_id, assumption_set, analysis_year)
);

CREATE TABLE IF NOT EXISTS evidence_financial_payback (
    financial_run_id TEXT NOT NULL,
    financial_case_id TEXT NOT NULL,
    assumption_set TEXT NOT NULL,
    simple_payback_year TEXT NOT NULL,
    discounted_payback_year TEXT NOT NULL,
    payback_status TEXT NOT NULL,
    within_horizon INTEGER NOT NULL,
    PRIMARY KEY (financial_run_id, financial_case_id, assumption_set)
);

CREATE TABLE IF NOT EXISTS evidence_financial_npv (
    financial_run_id TEXT NOT NULL,
    financial_case_id TEXT NOT NULL,
    assumption_set TEXT NOT NULL,
    npv REAL NOT NULL,
    discounted_initial_transition_cost REAL NOT NULL,
    discount_rate REAL NOT NULL,
    convention TEXT NOT NULL,
    PRIMARY KEY (financial_run_id, financial_case_id, assumption_set)
);

CREATE TABLE IF NOT EXISTS evidence_financial_cumulative_effects (
    financial_run_id TEXT NOT NULL,
    financial_case_id TEXT NOT NULL,
    assumption_set TEXT NOT NULL,
    one_year_effect REAL NOT NULL,
    three_year_cumulative_effect REAL NOT NULL,
    five_year_cumulative_effect REAL NOT NULL,
    discounted_three_year_effect REAL NOT NULL,
    discounted_five_year_effect REAL NOT NULL,
    PRIMARY KEY (financial_run_id, financial_case_id, assumption_set)
);

CREATE TABLE IF NOT EXISTS evidence_financial_sensitivity (
    financial_run_id TEXT NOT NULL,
    financial_case_id TEXT NOT NULL,
    sensitivity_parameter TEXT NOT NULL,
    sensitivity_level TEXT NOT NULL,
    sensitivity_value REAL NOT NULL,
    npv REAL NOT NULL,
    five_year_cumulative_effect REAL NOT NULL,
    readiness_status TEXT NOT NULL,
    tornado_impact REAL NOT NULL,
    PRIMARY KEY (financial_run_id, financial_case_id, sensitivity_parameter, sensitivity_level)
);

CREATE TABLE IF NOT EXISTS evidence_financial_break_even (
    financial_run_id TEXT NOT NULL,
    financial_case_id TEXT NOT NULL,
    break_even_metric TEXT NOT NULL,
    break_even_value REAL NOT NULL,
    interpretation TEXT NOT NULL,
    PRIMARY KEY (financial_run_id, financial_case_id, break_even_metric)
);

CREATE TABLE IF NOT EXISTS evidence_financial_risk_adjustments (
    financial_run_id TEXT NOT NULL,
    financial_case_id TEXT NOT NULL,
    factor_name TEXT NOT NULL,
    raw_factor_value REAL NOT NULL,
    adjusted_factor_value REAL NOT NULL,
    effect_on_realisability TEXT NOT NULL,
    evidence_source TEXT NOT NULL,
    PRIMARY KEY (financial_run_id, financial_case_id, factor_name)
);

CREATE TABLE IF NOT EXISTS evidence_financial_confidence (
    financial_run_id TEXT NOT NULL,
    financial_case_id TEXT NOT NULL,
    confidence_score REAL NOT NULL,
    confidence_status TEXT NOT NULL,
    readiness_status TEXT NOT NULL,
    operational_resilience_flag TEXT NOT NULL,
    not_realisable_without_mitigation INTEGER NOT NULL,
    PRIMARY KEY (financial_run_id, financial_case_id)
);

CREATE TABLE IF NOT EXISTS evidence_financial_comparison (
    financial_run_id TEXT NOT NULL,
    financial_case_id TEXT NOT NULL,
    assumption_set TEXT NOT NULL,
    baseline_recurring_cost REAL NOT NULL,
    case_recurring_cost REAL NOT NULL,
    gross_recurring_cost_difference REAL NOT NULL,
    recurring_mitigation_cost REAL NOT NULL,
    net_annual_financial_effect REAL NOT NULL,
    total_transition_cost REAL NOT NULL,
    npv REAL NOT NULL,
    risk_adjusted_npv REAL NOT NULL,
    five_year_cumulative_effect REAL NOT NULL,
    simple_payback_year TEXT NOT NULL,
    readiness_status TEXT NOT NULL,
    confidence_status TEXT NOT NULL,
    comparison_statement TEXT NOT NULL,
    PRIMARY KEY (financial_run_id, financial_case_id, assumption_set)
);

CREATE INDEX IF NOT EXISTS idx_financial_case ON evidence_financial_comparison(financial_run_id, financial_case_id);
CREATE INDEX IF NOT EXISTS idx_financial_cashflow_year ON evidence_financial_cashflows(financial_run_id, analysis_year);
CREATE INDEX IF NOT EXISTS idx_financial_sensitivity_parameter ON evidence_financial_sensitivity(financial_run_id, sensitivity_parameter);
CREATE INDEX IF NOT EXISTS idx_financial_readiness ON evidence_financial_comparison(financial_run_id, readiness_status);
