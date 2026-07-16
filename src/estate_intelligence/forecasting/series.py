"""Quality-gated monthly forecast-series construction."""

from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from typing import Any

from estate_intelligence.forecasting.aggregation import month_keys, room_hours
from estate_intelligence.forecasting.models import ForecastingConfig, ForecastSeries, SeriesPoint


def build_forecast_series(
    connection: sqlite3.Connection,
    config: ForecastingConfig,
    *,
    ingestion_run_id: str,
    quality_run_id: str,
    utilisation_run_id: str,
) -> list[ForecastSeries]:
    """Build configured monthly demand series from quality-gated evidence."""

    periods = month_keys("2024-04-01", config.reference_date)
    source_run_ids = json.dumps(
        {
            "ingestion_run_id": ingestion_run_id,
            "quality_run_id": quality_run_id,
            "utilisation_run_id": utilisation_run_id,
        },
        sort_keys=True,
    )
    activity = _included_activity(connection)
    workforce = _included_workforce(connection)
    series: list[ForecastSeries] = []
    for definition in config.series_definitions:
        if definition.source == "activity":
            series.extend(_activity_series(definition, activity, periods, source_run_ids))
        else:
            series.extend(_workforce_series(definition, workforce, periods, source_run_ids))
    return sorted(series, key=lambda item: item.series_id)


def _included_activity(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = [
        dict(row)
        for row in connection.execute(
            """
            SELECT activity.*
            FROM curated_clinical_activity AS activity
            JOIN evidence_analytics_population AS population
              ON population.dataset = 'clinical_activity'
             AND population.record_identifier = activity.activity_id
             AND population.analytical_status = 'included'
            ORDER BY activity.activity_date, activity.service_id, activity.activity_id
            """
        )
    ]
    return rows


def _included_workforce(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    return [
        dict(row)
        for row in connection.execute(
            """
            SELECT workforce.*
            FROM curated_workforce AS workforce
            JOIN evidence_analytics_population AS population
              ON population.dataset = 'workforce'
             AND population.record_identifier = workforce.workforce_record_id
             AND population.analytical_status = 'included'
            ORDER BY workforce.record_date, workforce.service_id, workforce.workforce_record_id
            """
        )
    ]


def _activity_series(
    definition: Any,
    rows: list[dict[str, Any]],
    periods: list[str],
    source_run_ids: str,
) -> list[ForecastSeries]:
    grouped: dict[tuple[str, str], dict[str, float | int]] = defaultdict(
        lambda: {"value": 0.0, "observations": 0}
    )
    for row in rows:
        period = str(row["activity_date"])[:7]
        service_id = str(row["service_id"])
        measure_value = _activity_measure(definition.measure, row)
        grouped[("estate", period)]["value"] = (
            float(grouped[("estate", period)]["value"]) + measure_value
        )
        grouped[("estate", period)]["observations"] = (
            int(grouped[("estate", period)]["observations"]) + 1
        )
        grouped[(service_id, period)]["value"] = (
            float(grouped[(service_id, period)]["value"]) + measure_value
        )
        grouped[(service_id, period)]["observations"] = (
            int(grouped[(service_id, period)]["observations"]) + 1
        )

    if definition.entity_type == "estate":
        return [
            _series_from_group(
                definition.target, "estate", "estate", periods, grouped, source_run_ids
            )
        ]
    service_ids = sorted({str(row["service_id"]) for row in rows})
    return [
        _series_from_group(
            definition.target, "service", service_id, periods, grouped, source_run_ids
        )
        for service_id in service_ids
    ]


def _workforce_series(
    definition: Any,
    rows: list[dict[str, Any]],
    periods: list[str],
    source_run_ids: str,
) -> list[ForecastSeries]:
    grouped: dict[tuple[str, str], dict[str, float | int]] = defaultdict(
        lambda: {"value": 0.0, "observations": 0}
    )
    for row in rows:
        period = str(row["record_date"])[:7]
        service_id = str(row["service_id"])
        grouped[(service_id, period)]["value"] = float(
            grouped[(service_id, period)]["value"]
        ) + float(row[definition.measure])
        grouped[(service_id, period)]["observations"] = (
            int(grouped[(service_id, period)]["observations"]) + 1
        )
    service_ids = sorted({str(row["service_id"]) for row in rows})
    return [
        _series_from_group(
            definition.target, "service", service_id, periods, grouped, source_run_ids
        )
        for service_id in service_ids
    ]


def _activity_measure(measure: str, row: dict[str, Any]) -> float:
    if measure == "face_to_face_room_hours":
        return room_hours(
            float(row["face_to_face_contacts"]),
            float(row["average_contact_duration_minutes"]),
        )
    if measure == "total_room_hour_demand":
        return room_hours(
            float(row["face_to_face_contacts"]),
            float(row["average_contact_duration_minutes"]),
        )
    return float(row[measure])


def _series_from_group(
    target: str,
    entity_type: str,
    entity_id: str,
    periods: list[str],
    grouped: dict[tuple[str, str], dict[str, float | int]],
    source_run_ids: str,
) -> ForecastSeries:
    points = []
    series_id = f"{target}|{entity_type}|{entity_id}"
    for period in periods:
        values = grouped[(entity_id, period)]
        observations = int(values["observations"])
        points.append(
            SeriesPoint(
                series_id=series_id,
                target=target,
                entity_type=entity_type,
                entity_id=entity_id,
                period=period,
                value=round(float(values["value"]), 4),
                observation_count=observations,
                quality_flag="none" if observations > 0 else "calendar_gap",
                imputation_flag="observed" if observations > 0 else "calendar_filled_zero",
                source_run_ids=source_run_ids,
            )
        )
    return ForecastSeries(
        series_id=series_id,
        target=target,
        entity_type=entity_type,
        entity_id=entity_id,
        points=tuple(points),
    )
