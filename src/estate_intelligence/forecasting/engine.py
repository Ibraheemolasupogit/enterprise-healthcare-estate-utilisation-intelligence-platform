"""Milestone 6 deterministic demand-forecasting engine."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

from estate_intelligence.forecasting.aggregation import next_months
from estate_intelligence.forecasting.backtesting import generate_folds
from estate_intelligence.forecasting.baseline import drift, moving_average, naive, seasonal_naive
from estate_intelligence.forecasting.eligibility import assess_eligibility
from estate_intelligence.forecasting.evaluation import metric_bundle
from estate_intelligence.forecasting.exponential_smoothing import (
    holt_linear,
    holt_winters_additive,
    simple_exponential_smoothing,
)
from estate_intelligence.forecasting.intervals import build_intervals, coverage
from estate_intelligence.forecasting.models import (
    EligibilityResult,
    ForecastingConfig,
    ForecastSeries,
    ModelResult,
    ModelSpec,
)
from estate_intelligence.forecasting.reporting import MODEL_CATALOGUE, export_forecast_evidence
from estate_intelligence.forecasting.selection import select_model
from estate_intelligence.forecasting.series import build_forecast_series
from estate_intelligence.ingestion.database import connect
from estate_intelligence.metrics.engine import verify_utilisation

FORECAST_TABLES = (
    "evidence_forecast_runs",
    "evidence_forecast_series",
    "evidence_forecast_eligibility",
    "evidence_forecast_folds",
    "evidence_forecast_model_results",
    "evidence_forecast_model_failures",
    "evidence_forecast_selections",
    "evidence_forecast_values",
    "evidence_forecast_intervals",
    "evidence_forecast_accuracy",
)


def run_forecasting(
    *,
    database_path: Path,
    config_path: Path = Path("config/forecasting.yaml"),
    output_dir: Path | None = None,
    rebuild: bool = False,
) -> dict[str, Any]:
    """Run deterministic demand forecasting and persist evidence."""

    verify_utilisation(database_path)
    config = ForecastingConfig.from_yaml(config_path)
    connection = connect(database_path)
    try:
        run_ids = _source_run_ids(connection)
        config_checksum = _file_checksum(config_path)
        model_checksum = _stable_checksum(MODEL_CATALOGUE)
        series_checksum = _stable_checksum(
            [definition.model_dump() for definition in config.series_definitions]
        )
        forecast_run_id = _forecast_run_id(
            config.framework_version,
            run_ids["ingestion_run_id"],
            run_ids["quality_run_id"],
            run_ids["utilisation_run_id"],
            config_checksum,
            model_checksum,
            series_checksum,
        )
        with connection:
            _create_forecast_tables(connection)
            if rebuild:
                _clear_forecast_tables(connection)
            elif _forecast_run_exists(connection, forecast_run_id):
                raise FileExistsError(
                    "Refusing to overwrite existing forecast evidence without --rebuild"
                )
            series = build_forecast_series(connection, config, **run_ids)
            evidence = _forecast_evidence(forecast_run_id, series, config)
            _insert_evidence(connection, evidence)
            periods = series[0].periods if series else []
            readiness = "forecast_ready" if evidence["selections"] else "review_required"
            connection.execute(
                """
                INSERT INTO evidence_forecast_runs
                (forecast_run_id, ingestion_run_id, quality_run_id, utilisation_run_id,
                 framework_version, config_checksum, model_catalogue_checksum,
                 series_catalogue_checksum, forecast_grain, forecast_horizon,
                 historical_start_period, historical_end_period, readiness_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    forecast_run_id,
                    run_ids["ingestion_run_id"],
                    run_ids["quality_run_id"],
                    run_ids["utilisation_run_id"],
                    config.framework_version,
                    config_checksum,
                    model_checksum,
                    series_checksum,
                    config.forecast_grain,
                    config.forecast_horizon,
                    periods[0] if periods else "",
                    periods[-1] if periods else "",
                    readiness,
                ),
            )
        exports: dict[str, str] = {}
        if output_dir is not None:
            exports = {
                name: str(path)
                for name, path in export_forecast_evidence(
                    connection, output_dir, forecast_run_id
                ).items()
            }
        return {
            "forecast_run_id": forecast_run_id,
            **run_ids,
            "config_checksum": config_checksum,
            "model_catalogue_checksum": model_checksum,
            "series_catalogue_checksum": series_checksum,
            "series_count": len(series),
            "selection_count": len(evidence["selections"]),
            "exports": exports,
        }
    finally:
        connection.close()


def verify_forecasting(database_path: Path) -> dict[str, Any]:
    """Verify persisted forecasting evidence."""

    connection = connect(database_path)
    try:
        run = connection.execute(
            "SELECT * FROM evidence_forecast_runs ORDER BY forecast_run_id LIMIT 1"
        ).fetchone()
        if run is None:
            raise ValueError("No forecast run evidence found")
        series_count = connection.execute(
            "SELECT COUNT(DISTINCT series_id) AS count FROM evidence_forecast_series"
        ).fetchone()["count"]
        value_count = connection.execute(
            "SELECT COUNT(*) AS count FROM evidence_forecast_values"
        ).fetchone()["count"]
        selection_count = connection.execute(
            "SELECT COUNT(*) AS count FROM evidence_forecast_selections"
        ).fetchone()["count"]
        if series_count == 0 or value_count == 0 or selection_count == 0:
            raise ValueError("Forecast evidence is incomplete")
        return {
            "forecast_run_id": run["forecast_run_id"],
            "readiness_status": run["readiness_status"],
            "series_count": series_count,
            "forecast_value_count": value_count,
            "selection_count": selection_count,
        }
    finally:
        connection.close()


def export_existing_forecast_evidence(database_path: Path, output_dir: Path) -> dict[str, Path]:
    """Export persisted forecasting evidence."""

    connection = connect(database_path)
    try:
        row = connection.execute(
            "SELECT forecast_run_id FROM evidence_forecast_runs ORDER BY forecast_run_id LIMIT 1"
        ).fetchone()
        if row is None:
            raise ValueError("No forecast run evidence found")
        return export_forecast_evidence(connection, output_dir, row["forecast_run_id"])
    finally:
        connection.close()


def _forecast_evidence(
    forecast_run_id: str, series: list[ForecastSeries], config: ForecastingConfig
) -> dict[str, list[dict[str, Any]]]:
    rows: dict[str, list[dict[str, Any]]] = {
        "series": [],
        "eligibility": [],
        "folds": [],
        "results": [],
        "failures": [],
        "selections": [],
        "values": [],
        "intervals": [],
        "accuracy": [],
    }
    future_periods = next_months(series[0].periods[-1], config.forecast_horizon) if series else []
    for item in series:
        rows["series"].extend(_series_rows(forecast_run_id, item))
        eligibility = assess_eligibility(item, config)
        rows["eligibility"].append(_eligibility_row(forecast_run_id, eligibility))
        folds = generate_folds(
            item.periods,
            config.initial_training_periods,
            config.validation_horizon,
            config.rolling_step,
        )
        rows["folds"].extend(_fold_rows(forecast_run_id, item, folds))
        results, failures = _evaluate_models(item, eligibility, folds, config)
        rows["results"].extend(_result_rows(forecast_run_id, item.series_id, results))
        rows["failures"].extend(
            {
                "forecast_run_id": forecast_run_id,
                "series_id": item.series_id,
                "model_id": model_id,
                "failure_reason": reason,
            }
            for model_id, reason in failures
        )
        selection = select_model(item.series_id, results, config.selection_metric)
        rows["selections"].append(
            {
                "forecast_run_id": forecast_run_id,
                "series_id": item.series_id,
                "selected_model_id": selection.selected_model_id,
                "primary_metric": selection.primary_metric,
                "primary_metric_value": selection.primary_metric_value,
                "baseline_model_id": selection.baseline_model_id,
                "baseline_metric_value": selection.baseline_metric_value,
                "baseline_beaten_flag": 1 if selection.baseline_beaten_flag else 0,
                "selection_reason": selection.selection_reason,
            }
        )
        selected_result = next(
            (result for result in results if result.model_id == selection.selected_model_id),
            results[0],
        )
        final_forecast = _forecast_model(
            selected_result.model_id,
            item.values,
            config.forecast_horizon,
            config,
            selected_result.parameters,
        )
        residuals = [
            actual - forecast
            for actual, forecast in zip(
                selected_result.actuals, selected_result.forecasts, strict=True
            )
        ]
        for step, (period, forecast_value) in enumerate(
            zip(future_periods, final_forecast, strict=True), start=1
        ):
            rows["values"].append(
                {
                    "forecast_run_id": forecast_run_id,
                    "series_id": item.series_id,
                    "target": item.target,
                    "entity_type": item.entity_type,
                    "entity_id": item.entity_id,
                    "period": period,
                    "horizon_step": step,
                    "model_id": selection.selected_model_id,
                    "forecast_value": round(forecast_value, config.rounding["decimal_places"]),
                    "actual_value": None,
                    "value_type": "future_forecast",
                }
            )
        for interval in build_intervals(
            final_forecast, residuals, config.prediction_interval_levels
        ):
            step = int(interval["horizon_step"])
            rows["intervals"].append(
                {
                    "forecast_run_id": forecast_run_id,
                    "series_id": item.series_id,
                    "period": future_periods[step - 1],
                    "model_id": selection.selected_model_id,
                    **interval,
                }
            )
        rows["accuracy"].extend(_accuracy_rows(forecast_run_id, item.series_id, results))
    return rows


def _evaluate_models(
    series: ForecastSeries,
    eligibility: EligibilityResult,
    folds: list[Any],
    config: ForecastingConfig,
) -> tuple[list[ModelResult], list[tuple[str, str]]]:
    results: list[ModelResult] = []
    failures: list[tuple[str, str]] = []
    for spec in config.model_catalogue:
        reason = _model_ineligible_reason(spec, eligibility, series, config)
        if reason is not None:
            failures.append((spec.model_id, reason))
            continue
        forecasts: list[float] = []
        actuals: list[float] = []
        for fold in folds:
            train = series.values[fold.train_start : fold.train_end]
            actual = series.values[fold.validation_start : fold.validation_end]
            forecast = _forecast_model(spec.model_id, train, len(actual), config, spec.parameters)
            forecasts.extend(forecast)
            actuals.extend(actual)
        metrics = metric_bundle(
            actuals, forecasts, series.values[: config.initial_training_periods]
        )
        residuals = [actual - forecast for actual, forecast in zip(actuals, forecasts, strict=True)]
        metrics["interval_coverage_80"] = coverage(actuals, forecasts, residuals, 0.8)
        metrics["interval_coverage_95"] = coverage(actuals, forecasts, residuals, 0.95)
        results.append(
            ModelResult(
                model_id=spec.model_id,
                parameters=dict(spec.parameters),
                forecasts=tuple(forecasts),
                actuals=tuple(actuals),
                evaluated_fold_count=len(folds),
                metrics=metrics,
                model_status="evaluated",
            )
        )
    if not results:
        forecast = naive(
            series.values[: config.initial_training_periods], config.validation_horizon
        )
        actual = series.values[
            config.initial_training_periods : config.initial_training_periods
            + config.validation_horizon
        ]
        results.append(
            ModelResult(
                model_id="naive",
                parameters={},
                forecasts=tuple(forecast),
                actuals=tuple(actual),
                evaluated_fold_count=1,
                metrics=metric_bundle(
                    actual, forecast, series.values[: config.initial_training_periods]
                ),
                model_status="evaluated",
            )
        )
    return results, failures


def _model_ineligible_reason(
    spec: ModelSpec,
    eligibility: EligibilityResult,
    series: ForecastSeries,
    config: ForecastingConfig,
) -> str | None:
    baseline_models = {"naive", "seasonal_naive", "moving_average", "drift"}
    if eligibility.eligibility_status not in {"eligible", "baseline_only", "constant_series"}:
        return f"series eligibility is {eligibility.eligibility_status}"
    if eligibility.eligibility_status != "eligible" and spec.model_id not in baseline_models:
        return f"model restricted by {eligibility.eligibility_status}"
    if len(series.values) < spec.minimum_periods:
        return "insufficient periods for model"
    if spec.requires_non_constant and eligibility.variance == 0:
        return "model requires non-constant history"
    if spec.requires_seasonality and len(series.values) < config.seasonal_period * 2:
        return "model requires two seasonal cycles"
    if spec.requires_seasonality and spec.model_id == "holt_winters_additive":
        if config.initial_training_periods < config.seasonal_period * 2:
            return "validation folds do not contain two seasonal cycles"
    if spec.model_id == "seasonal_naive" and len(series.values) < config.seasonal_period:
        return "seasonal naive requires one seasonal cycle"
    return None


def _forecast_model(
    model_id: str,
    values: list[float],
    horizon: int,
    config: ForecastingConfig,
    parameters: dict[str, Any],
) -> list[float]:
    if model_id == "naive":
        return naive(values, horizon)
    if model_id == "seasonal_naive":
        return seasonal_naive(values, horizon, config.seasonal_period)
    if model_id == "moving_average":
        return moving_average(values, horizon, int(parameters.get("window", 3)))
    if model_id == "drift":
        return drift(values, horizon)
    if model_id == "simple_exponential_smoothing":
        return simple_exponential_smoothing(values, horizon, float(parameters.get("alpha", 0.4)))
    if model_id == "holt_linear":
        return holt_linear(
            values,
            horizon,
            float(parameters.get("alpha", 0.5)),
            float(parameters.get("beta", 0.2)),
        )
    if model_id == "holt_winters_additive":
        return holt_winters_additive(
            values,
            horizon,
            config.seasonal_period,
            float(parameters.get("alpha", 0.4)),
            float(parameters.get("beta", 0.1)),
            float(parameters.get("gamma", 0.1)),
        )
    raise ValueError(f"Unknown model_id: {model_id}")


def _series_rows(forecast_run_id: str, series: ForecastSeries) -> list[dict[str, Any]]:
    return [{**point.__dict__, "forecast_run_id": forecast_run_id} for point in series.points]


def _eligibility_row(forecast_run_id: str, result: EligibilityResult) -> dict[str, Any]:
    row = {**result.__dict__, "forecast_run_id": forecast_run_id}
    row["recent_activity_flag"] = 1 if result.recent_activity_flag else 0
    return row


def _fold_rows(
    forecast_run_id: str, series: ForecastSeries, folds: list[Any]
) -> list[dict[str, Any]]:
    rows = []
    periods = series.periods
    for fold in folds:
        rows.append(
            {
                "forecast_run_id": forecast_run_id,
                "series_id": series.series_id,
                "fold_id": fold.fold_id,
                "fold_number": fold.fold_number,
                "training_start_period": periods[fold.train_start],
                "training_end_period": periods[fold.train_end - 1],
                "validation_start_period": periods[fold.validation_start],
                "validation_end_period": periods[fold.validation_end - 1],
                "training_periods": fold.train_end - fold.train_start,
                "validation_periods": fold.validation_end - fold.validation_start,
            }
        )
    return rows


def _result_rows(
    forecast_run_id: str, series_id: str, results: list[ModelResult]
) -> list[dict[str, Any]]:
    rows = []
    for result in results:
        rows.append(
            {
                "forecast_run_id": forecast_run_id,
                "series_id": series_id,
                "model_id": result.model_id,
                "model_parameters": json.dumps(result.parameters, sort_keys=True),
                "evaluated_fold_count": result.evaluated_fold_count,
                "mae": result.metrics.get("mae"),
                "rmse": result.metrics.get("rmse"),
                "wape": result.metrics.get("wape"),
                "bias": result.metrics.get("bias"),
                "signed_percentage_bias": result.metrics.get("signed_percentage_bias"),
                "smape": result.metrics.get("smape"),
                "mase": result.metrics.get("mase"),
                "interval_coverage_80": result.metrics.get("interval_coverage_80"),
                "interval_coverage_95": result.metrics.get("interval_coverage_95"),
                "model_status": result.model_status,
            }
        )
    return rows


def _accuracy_rows(
    forecast_run_id: str, series_id: str, results: list[ModelResult]
) -> list[dict[str, Any]]:
    rows = []
    for result in results:
        for metric_name, value in sorted(result.metrics.items()):
            rows.append(
                {
                    "forecast_run_id": forecast_run_id,
                    "series_id": series_id,
                    "model_id": result.model_id,
                    "metric_name": metric_name,
                    "metric_value": value,
                    "metric_status": "defined" if value is not None else "not_applicable",
                }
            )
    return rows


def _insert_evidence(
    connection: sqlite3.Connection, evidence: dict[str, list[dict[str, Any]]]
) -> None:
    mapping = {
        "series": "evidence_forecast_series",
        "eligibility": "evidence_forecast_eligibility",
        "folds": "evidence_forecast_folds",
        "results": "evidence_forecast_model_results",
        "failures": "evidence_forecast_model_failures",
        "selections": "evidence_forecast_selections",
        "values": "evidence_forecast_values",
        "intervals": "evidence_forecast_intervals",
        "accuracy": "evidence_forecast_accuracy",
    }
    for key, table in mapping.items():
        _insert_rows(connection, table, evidence[key])


def _insert_rows(connection: sqlite3.Connection, table: str, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    table_columns = {
        row["name"] for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
    }
    for row in rows:
        clean = {key: value for key, value in row.items() if key in table_columns}
        columns = list(clean)
        placeholders = ", ".join("?" for _ in columns)
        connection.execute(
            f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})",
            tuple(clean[column] for column in columns),
        )


def _create_forecast_tables(connection: sqlite3.Connection) -> None:
    connection.executescript(
        Path("database/schema/008_forecasting_tables.sql").read_text(encoding="utf-8")
    )


def _clear_forecast_tables(connection: sqlite3.Connection) -> None:
    for table in FORECAST_TABLES:
        connection.execute(f"DELETE FROM {table}")


def _forecast_run_exists(connection: sqlite3.Connection, forecast_run_id: str) -> bool:
    return (
        connection.execute(
            "SELECT forecast_run_id FROM evidence_forecast_runs WHERE forecast_run_id = ?",
            (forecast_run_id,),
        ).fetchone()
        is not None
    )


def _source_run_ids(connection: sqlite3.Connection) -> dict[str, str]:
    ingestion = connection.execute(
        "SELECT ingestion_run_id FROM evidence_ingestion_runs ORDER BY ingestion_run_id LIMIT 1"
    ).fetchone()
    quality = connection.execute(
        "SELECT quality_run_id FROM evidence_quality_runs ORDER BY quality_run_id LIMIT 1"
    ).fetchone()
    utilisation = connection.execute(
        """
        SELECT utilisation_run_id
        FROM evidence_utilisation_runs
        ORDER BY utilisation_run_id
        LIMIT 1
        """
    ).fetchone()
    if ingestion is None or quality is None or utilisation is None:
        raise ValueError(
            "Ingestion, quality and utilisation evidence are required before forecasting"
        )
    return {
        "ingestion_run_id": str(ingestion["ingestion_run_id"]),
        "quality_run_id": str(quality["quality_run_id"]),
        "utilisation_run_id": str(utilisation["utilisation_run_id"]),
    }


def _forecast_run_id(*parts: str) -> str:
    digest = hashlib.sha256(json.dumps(parts, sort_keys=True).encode()).hexdigest()
    return f"FCT-{digest[:16]}"


def _file_checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _stable_checksum(payload: object) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
