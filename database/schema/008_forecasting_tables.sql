CREATE TABLE IF NOT EXISTS evidence_forecast_runs (
    forecast_run_id TEXT PRIMARY KEY,
    ingestion_run_id TEXT NOT NULL,
    quality_run_id TEXT NOT NULL,
    utilisation_run_id TEXT NOT NULL,
    framework_version TEXT NOT NULL,
    config_checksum TEXT NOT NULL,
    model_catalogue_checksum TEXT NOT NULL,
    series_catalogue_checksum TEXT NOT NULL,
    forecast_grain TEXT NOT NULL,
    forecast_horizon INTEGER NOT NULL,
    historical_start_period TEXT NOT NULL,
    historical_end_period TEXT NOT NULL,
    readiness_status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence_forecast_series (
    forecast_run_id TEXT NOT NULL,
    series_id TEXT NOT NULL,
    target TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    period TEXT NOT NULL,
    value REAL NOT NULL,
    observation_count INTEGER NOT NULL,
    quality_flag TEXT NOT NULL,
    imputation_flag TEXT NOT NULL,
    source_run_ids TEXT NOT NULL,
    PRIMARY KEY (forecast_run_id, series_id, period)
);

CREATE TABLE IF NOT EXISTS evidence_forecast_eligibility (
    forecast_run_id TEXT NOT NULL,
    series_id TEXT NOT NULL,
    target TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    eligibility_status TEXT NOT NULL,
    reason TEXT NOT NULL,
    historical_periods INTEGER NOT NULL,
    non_zero_periods INTEGER NOT NULL,
    missing_period_ratio REAL NOT NULL,
    variance REAL NOT NULL,
    non_zero_ratio REAL NOT NULL,
    average_interval_between_non_zero_periods REAL,
    squared_coefficient_of_variation REAL,
    recent_activity_flag INTEGER NOT NULL,
    PRIMARY KEY (forecast_run_id, series_id)
);

CREATE TABLE IF NOT EXISTS evidence_forecast_folds (
    forecast_run_id TEXT NOT NULL,
    series_id TEXT NOT NULL,
    fold_id TEXT NOT NULL,
    fold_number INTEGER NOT NULL,
    training_start_period TEXT NOT NULL,
    training_end_period TEXT NOT NULL,
    validation_start_period TEXT NOT NULL,
    validation_end_period TEXT NOT NULL,
    training_periods INTEGER NOT NULL,
    validation_periods INTEGER NOT NULL,
    PRIMARY KEY (forecast_run_id, series_id, fold_id)
);

CREATE TABLE IF NOT EXISTS evidence_forecast_model_results (
    forecast_run_id TEXT NOT NULL,
    series_id TEXT NOT NULL,
    model_id TEXT NOT NULL,
    model_parameters TEXT NOT NULL,
    evaluated_fold_count INTEGER NOT NULL,
    mae REAL,
    rmse REAL,
    wape REAL,
    bias REAL,
    signed_percentage_bias REAL,
    smape REAL,
    mase REAL,
    interval_coverage_80 REAL,
    interval_coverage_95 REAL,
    model_status TEXT NOT NULL,
    PRIMARY KEY (forecast_run_id, series_id, model_id)
);

CREATE TABLE IF NOT EXISTS evidence_forecast_model_failures (
    forecast_run_id TEXT NOT NULL,
    series_id TEXT NOT NULL,
    model_id TEXT NOT NULL,
    failure_reason TEXT NOT NULL,
    PRIMARY KEY (forecast_run_id, series_id, model_id)
);

CREATE TABLE IF NOT EXISTS evidence_forecast_selections (
    forecast_run_id TEXT NOT NULL,
    series_id TEXT NOT NULL,
    selected_model_id TEXT NOT NULL,
    primary_metric TEXT NOT NULL,
    primary_metric_value REAL,
    baseline_model_id TEXT NOT NULL,
    baseline_metric_value REAL,
    baseline_beaten_flag INTEGER NOT NULL,
    selection_reason TEXT NOT NULL,
    PRIMARY KEY (forecast_run_id, series_id)
);

CREATE TABLE IF NOT EXISTS evidence_forecast_values (
    forecast_run_id TEXT NOT NULL,
    series_id TEXT NOT NULL,
    target TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    period TEXT NOT NULL,
    horizon_step INTEGER NOT NULL,
    model_id TEXT NOT NULL,
    forecast_value REAL NOT NULL,
    actual_value REAL,
    value_type TEXT NOT NULL,
    PRIMARY KEY (forecast_run_id, series_id, period, value_type)
);

CREATE TABLE IF NOT EXISTS evidence_forecast_intervals (
    forecast_run_id TEXT NOT NULL,
    series_id TEXT NOT NULL,
    period TEXT NOT NULL,
    horizon_step INTEGER NOT NULL,
    model_id TEXT NOT NULL,
    interval_level REAL NOT NULL,
    lower_bound REAL NOT NULL,
    upper_bound REAL NOT NULL,
    interval_method TEXT NOT NULL,
    PRIMARY KEY (forecast_run_id, series_id, period, interval_level)
);

CREATE TABLE IF NOT EXISTS evidence_forecast_accuracy (
    forecast_run_id TEXT NOT NULL,
    series_id TEXT NOT NULL,
    model_id TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value REAL,
    metric_status TEXT NOT NULL,
    PRIMARY KEY (forecast_run_id, series_id, model_id, metric_name)
);

CREATE INDEX IF NOT EXISTS idx_forecast_series_target
    ON evidence_forecast_series (forecast_run_id, target, entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_forecast_values_target
    ON evidence_forecast_values (forecast_run_id, target, entity_type, entity_id, period);
CREATE INDEX IF NOT EXISTS idx_forecast_eligibility_status
    ON evidence_forecast_eligibility (forecast_run_id, eligibility_status);
