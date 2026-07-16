"""Milestone 5 deterministic utilisation analytics engine."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

from estate_intelligence.ingestion.database import connect
from estate_intelligence.metrics.activity import contacts_per_hour
from estate_intelligence.metrics.availability import applicable_weeks, available_room_hours
from estate_intelligence.metrics.finance import annual_operating_cost, unit_cost
from estate_intelligence.metrics.models import UtilisationConfig
from estate_intelligence.metrics.reporting import METRIC_CATALOGUE, export_utilisation_evidence
from estate_intelligence.metrics.scoring import (
    persistent_underutilisation_flag,
    readiness_status,
)
from estate_intelligence.metrics.time_bands import assign_time_band, is_peak_band
from estate_intelligence.metrics.utilisation import (
    actual_occupied_utilisation,
    attendance_utilisation,
    booked_utilisation,
    effective_utilisation_score,
    safe_divide,
)
from estate_intelligence.metrics.workforce import (
    contacts_per_available_fte,
    workforce_availability_ratio,
)
from estate_intelligence.validation.engine import verify_data_quality

ID_COLUMNS = {
    "buildings": "building_id",
    "rooms": "room_id",
    "services": "service_id",
    "bookings": "booking_id",
    "clinical_activity": "activity_id",
    "workforce": "workforce_record_id",
    "finance": "finance_record_id",
    "accessibility": "accessibility_record_id",
}


def calculate_utilisation(
    *,
    database_path: Path,
    config_path: Path = Path("config/utilisation.yaml"),
    output_dir: Path | None = None,
    rebuild: bool = False,
) -> dict[str, Any]:
    """Calculate deterministic utilisation evidence."""

    verify_data_quality(database_path)
    config = UtilisationConfig.from_yaml(config_path)
    config_checksum = _file_checksum(config_path)
    formula_checksum = _formula_catalogue_checksum()
    connection = connect(database_path)
    try:
        run_row = connection.execute(
            "SELECT ingestion_run_id FROM evidence_ingestion_runs ORDER BY ingestion_run_id LIMIT 1"
        ).fetchone()
        quality_row = connection.execute(
            "SELECT quality_run_id FROM evidence_quality_runs ORDER BY quality_run_id LIMIT 1"
        ).fetchone()
        if run_row is None or quality_row is None:
            raise ValueError("Ingestion and quality evidence are required before utilisation")
        ingestion_run_id = run_row["ingestion_run_id"]
        quality_run_id = quality_row["quality_run_id"]
        utilisation_run_id = _utilisation_run_id(
            config.framework_version,
            ingestion_run_id,
            quality_run_id,
            config_checksum,
            formula_checksum,
        )
        with connection:
            _create_utilisation_tables(connection)
            if rebuild:
                _clear_utilisation_tables(connection)
            elif _utilisation_run_exists(connection, utilisation_run_id):
                raise FileExistsError(
                    "Refusing to overwrite existing utilisation evidence without --rebuild"
                )
            evidence = _build_evidence(connection, utilisation_run_id, config)
            _insert_evidence(connection, utilisation_run_id, evidence)
            summary = evidence["summary"]
            connection.execute(
                """
                INSERT INTO evidence_utilisation_runs
                (utilisation_run_id, ingestion_run_id, quality_run_id, framework_version,
                 config_checksum, formula_catalogue_checksum, overall_available_hours,
                 overall_booked_utilisation, overall_actual_utilisation,
                 overall_effective_utilisation, readiness_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    utilisation_run_id,
                    ingestion_run_id,
                    quality_run_id,
                    config.framework_version,
                    config_checksum,
                    formula_checksum,
                    summary["available_hours"],
                    summary["booked_utilisation"],
                    summary["actual_utilisation"],
                    summary["effective_utilisation"],
                    readiness_status(summary["effective_utilisation"]),
                ),
            )
        exports: dict[str, str] = {}
        if output_dir is not None:
            exports = {
                name: str(path)
                for name, path in export_utilisation_evidence(
                    connection, output_dir, utilisation_run_id
                ).items()
            }
        return {
            "utilisation_run_id": utilisation_run_id,
            "ingestion_run_id": ingestion_run_id,
            "quality_run_id": quality_run_id,
            "config_checksum": config_checksum,
            "formula_catalogue_checksum": formula_checksum,
            "summary": summary,
            "exports": exports,
        }
    finally:
        connection.close()


def verify_utilisation(database_path: Path) -> dict[str, Any]:
    """Verify persisted utilisation evidence."""

    connection = connect(database_path)
    try:
        run = connection.execute(
            "SELECT * FROM evidence_utilisation_runs ORDER BY utilisation_run_id LIMIT 1"
        ).fetchone()
        if run is None:
            raise ValueError("No utilisation run evidence found")
        room_count = connection.execute(
            "SELECT COUNT(*) AS count FROM evidence_room_utilisation"
        ).fetchone()["count"]
        exclusion_count = connection.execute(
            "SELECT COUNT(*) AS count FROM evidence_analytics_exclusions"
        ).fetchone()["count"]
        return {
            "utilisation_run_id": run["utilisation_run_id"],
            "readiness_status": run["readiness_status"],
            "overall_effective_utilisation": run["overall_effective_utilisation"],
            "room_count": room_count,
            "exclusion_count": exclusion_count,
        }
    finally:
        connection.close()


def export_existing_utilisation_evidence(database_path: Path, output_dir: Path) -> dict[str, Path]:
    """Export existing utilisation evidence."""

    connection = connect(database_path)
    try:
        row = connection.execute(
            """
            SELECT utilisation_run_id
            FROM evidence_utilisation_runs
            ORDER BY utilisation_run_id
            LIMIT 1
            """
        ).fetchone()
        if row is None:
            raise ValueError("No utilisation run evidence found")
        return export_utilisation_evidence(connection, output_dir, row["utilisation_run_id"])
    finally:
        connection.close()


def _build_evidence(
    connection: sqlite3.Connection, utilisation_run_id: str, config: UtilisationConfig
) -> dict[str, Any]:
    population, exclusions, excluded = _analytical_population(
        connection, utilisation_run_id, config
    )
    rooms = [
        row for row in _rows(connection, "curated_rooms") if row["room_id"] not in excluded["rooms"]
    ]
    bookings = [
        row
        for row in _rows(connection, "curated_bookings")
        if row["booking_id"] not in excluded["bookings"] and row["room_id"] not in excluded["rooms"]
    ]
    activity = [
        row
        for row in _rows(connection, "curated_clinical_activity")
        if row["activity_id"] not in excluded["clinical_activity"]
        and row["room_id"] not in excluded["rooms"]
    ]
    workforce = [
        row
        for row in _rows(connection, "curated_workforce")
        if row["workforce_record_id"] not in excluded["workforce"]
    ]
    finance = [
        row
        for row in _rows(connection, "curated_finance")
        if row["finance_record_id"] not in excluded["finance"]
    ]
    buildings = {row["building_id"]: row for row in _rows(connection, "curated_buildings")}
    services = {row["service_id"]: row for row in _rows(connection, "curated_services")}
    period_start = date.fromisoformat(config.analysis_period["start_date"])
    period_end = date.fromisoformat(config.analysis_period["end_date"])
    weeks = applicable_weeks(period_start, period_end)
    room_rows = _room_metrics(rooms, bookings, activity, buildings, workforce, config, weeks)
    building_rows = _aggregate_buildings(room_rows)
    site_rows = _aggregate_sites(room_rows)
    service_rows = _service_metrics(bookings, activity, workforce, services)
    room_service_rows = _room_service_metrics(bookings, activity)
    time_band_rows = _time_band_metrics(bookings, config)
    monthly_rows = _monthly_metrics(rooms, bookings, period_start, period_end, config)
    under_rows = _underutilisation(room_rows, monthly_rows, config)
    cost_rows = _unit_costs(finance, building_rows, excluded["finance"], connection, config)
    summary = _summary(room_rows, service_rows)
    return {
        "population": population,
        "exclusions": exclusions,
        "rooms": room_rows,
        "buildings": building_rows,
        "sites": site_rows,
        "services": service_rows,
        "room_services": room_service_rows,
        "time_bands": time_band_rows,
        "monthly": monthly_rows,
        "underutilisation": under_rows,
        "costs": cost_rows,
        "summary": summary,
    }


def _analytical_population(
    connection: sqlite3.Connection, utilisation_run_id: str, config: UtilisationConfig
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, set[str]]]:
    manual = [
        dict(row)
        for row in connection.execute(
            """
            SELECT dataset, record_identifier, rule_id, severity, failure_action
            FROM evidence_quality_record_issues
            WHERE failure_action = 'manual_review'
            ORDER BY dataset, record_identifier, rule_id
            """
        )
    ]
    excluded: dict[str, set[str]] = {dataset: set() for dataset in ID_COLUMNS}
    exclusions: list[dict[str, Any]] = []
    for issue in manual:
        if config.quality_policy.manual_review.get(str(issue["severity"]), "exclude") == "exclude":
            dataset = str(issue["dataset"])
            record_id = str(issue["record_identifier"])
            excluded[dataset].add(record_id)
            exclusions.append(
                {
                    "utilisation_run_id": utilisation_run_id,
                    "dataset": dataset,
                    "record_identifier": record_id,
                    "rule_id": issue["rule_id"],
                    "severity": issue["severity"],
                    "failure_action": issue["failure_action"],
                    "reason": "manual_review_excluded_by_policy",
                    "analytical_effect": "record_removed_from_metric_population",
                }
            )
    for booking in _rows(connection, "curated_bookings"):
        if booking["room_id"] in excluded["rooms"]:
            excluded["bookings"].add(booking["booking_id"])
            exclusions.append(
                _cascade(utilisation_run_id, "bookings", booking["booking_id"], "room_excluded")
            )
    for row in _rows(connection, "curated_clinical_activity"):
        if row["room_id"] in excluded["rooms"]:
            excluded["clinical_activity"].add(row["activity_id"])
            exclusions.append(
                _cascade(
                    utilisation_run_id, "clinical_activity", row["activity_id"], "room_excluded"
                )
            )
    population: list[dict[str, Any]] = []
    for dataset, id_column in ID_COLUMNS.items():
        for row in _rows(connection, f"curated_{dataset}"):
            record_id = str(row[id_column])
            status = str(row["record_status"])
            analytical_status = "excluded" if record_id in excluded[dataset] else "included"
            if status not in config.quality_policy.allowed_record_statuses:
                analytical_status = "excluded"
            population.append(
                {
                    "utilisation_run_id": utilisation_run_id,
                    "dataset": dataset,
                    "record_identifier": record_id,
                    "record_status": status,
                    "analytical_status": analytical_status,
                    "quality_flag": str(row["warning_reason"] or "none"),
                }
            )
    return population, exclusions, excluded


def _room_metrics(
    rooms: list[dict[str, Any]],
    bookings: list[dict[str, Any]],
    activity: list[dict[str, Any]],
    buildings: dict[str, dict[str, Any]],
    workforce: list[dict[str, Any]],
    config: UtilisationConfig,
    weeks: float,
) -> list[dict[str, Any]]:
    bookings_by_room = _group(bookings, "room_id")
    activity_by_room = _group(activity, "room_id")
    workforce_by_site = _group(workforce, "site_id")
    rows = []
    for room in sorted(rooms, key=lambda row: row["room_id"]):
        building = buildings[str(room["building_id"])]
        site_id = str(building["site_id"])
        room_bookings = bookings_by_room[str(room["room_id"])]
        room_activity = activity_by_room[str(room["room_id"])]
        available = available_room_hours(
            float(room["available_hours_per_week"]),
            weeks,
            str(room["active_flag"]).lower() == "true",
        )
        scheduled_hours = sum(_duration_hours(row) for row in room_bookings)
        booked_hours = sum(
            _duration_hours(row) for row in room_bookings if not _bool(row["cancellation_flag"])
        )
        occupied_hours = sum(_duration_hours(row) for row in room_bookings if _occupied(row))
        planned = sum(
            int(row["planned_attendance_count"])
            for row in room_bookings
            if not _bool(row["cancellation_flag"])
        )
        actual = sum(
            int(row["actual_attendance_count"])
            for row in room_bookings
            if not _bool(row["cancellation_flag"])
        )
        completed = sum(int(row["completed_contacts"]) for row in room_activity)
        workforce_ratio = _site_workforce_ratio(workforce_by_site[site_id])
        cancel_rate = safe_divide(
            sum(1 for row in room_bookings if _bool(row["cancellation_flag"])),
            len(room_bookings),
        )
        no_show_rate = safe_divide(
            sum(1 for row in room_bookings if _bool(row["no_show_flag"])), len(room_bookings)
        )
        contacts_factor = min(contacts_per_hour(completed, available), 1.0)
        components = {
            "actual_occupied_utilisation": actual_occupied_utilisation(occupied_hours, available),
            "attendance_utilisation": attendance_utilisation(actual, planned),
            "contacts_per_available_hour_factor": contacts_factor,
            "workforce_availability_factor": workforce_ratio,
            "cancellation_penalty_factor": 1 - cancel_rate,
            "no_show_penalty_factor": 1 - no_show_rate,
        }
        rows.append(
            {
                "utilisation_run_id": "",
                "room_id": room["room_id"],
                "building_id": room["building_id"],
                "site_id": site_id,
                "available_hours": _round(available, config),
                "booked_hours": _round(booked_hours, config),
                "occupied_hours": _round(occupied_hours, config),
                "booked_utilisation": _round(booked_utilisation(booked_hours, available), config),
                "actual_utilisation": _round(
                    actual_occupied_utilisation(occupied_hours, available), config
                ),
                "attendance_utilisation": _round(attendance_utilisation(actual, planned), config),
                "effective_utilisation": _round(
                    effective_utilisation_score(components, config.formula_weights), config
                ),
                "completed_contacts": completed,
                "protected_capacity_flag": 1 if _bool(room["protected_capacity_flag"]) else 0,
                "quality_flag": str(room["warning_reason"] or "none"),
                "scheduled_booking_hours": _round(scheduled_hours, config),
                "planned_attendance": planned,
                "actual_attendance": actual,
            }
        )
    return rows


def _aggregate_buildings(room_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return _aggregate_entity(room_rows, "building_id", ("building_id", "site_id"))


def _aggregate_sites(room_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return _aggregate_entity(room_rows, "site_id", ("site_id",))


def _aggregate_entity(
    room_rows: list[dict[str, Any]], key: str, fields: tuple[str, ...]
) -> list[dict[str, Any]]:
    grouped = _group(room_rows, key)
    results = []
    for value, rows in sorted(grouped.items()):
        available = sum(float(row["available_hours"]) for row in rows)
        booked = sum(float(row["booked_hours"]) for row in rows)
        occupied = sum(float(row["occupied_hours"]) for row in rows)
        completed = sum(int(row["completed_contacts"]) for row in rows)
        result = {
            "utilisation_run_id": "",
            fields[0]: value,
            "available_hours": round(available, 4),
            "booked_hours": round(booked, 4),
            "occupied_hours": round(occupied, 4),
            "booked_utilisation": round(booked_utilisation(booked, available), 4),
            "actual_utilisation": round(actual_occupied_utilisation(occupied, available), 4),
            "effective_utilisation": round(
                sum(float(row["effective_utilisation"]) for row in rows) / len(rows), 4
            ),
            "completed_contacts": completed,
        }
        if "site_id" in fields and key != "site_id":
            result["site_id"] = str(rows[0]["site_id"])
        results.append(result)
    return results


def _service_metrics(
    bookings: list[dict[str, Any]],
    activity: list[dict[str, Any]],
    workforce: list[dict[str, Any]],
    services: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    bookings_by_service = _group(bookings, "service_id")
    activity_by_service = _group(activity, "service_id")
    workforce_by_service = _group(workforce, "service_id")
    rows = []
    for service_id, service in sorted(services.items()):
        service_bookings = bookings_by_service[service_id]
        service_activity = activity_by_service[service_id]
        service_workforce = workforce_by_service[service_id]
        booked = sum(
            _duration_hours(row) for row in service_bookings if not _bool(row["cancellation_flag"])
        )
        occupied = sum(_duration_hours(row) for row in service_bookings if _occupied(row))
        planned = sum(
            int(row["planned_attendance_count"])
            for row in service_bookings
            if not _bool(row["cancellation_flag"])
        )
        actual = sum(
            int(row["actual_attendance_count"])
            for row in service_bookings
            if not _bool(row["cancellation_flag"])
        )
        completed = sum(int(row["completed_contacts"]) for row in service_activity)
        available_fte = sum(float(row["available_fte"]) for row in service_workforce)
        rows.append(
            {
                "utilisation_run_id": "",
                "service_id": service_id,
                "service_name": service["service_name"],
                "booked_hours": round(booked, 4),
                "occupied_hours": round(occupied, 4),
                "planned_attendance": planned,
                "actual_attendance": actual,
                "completed_contacts": completed,
                "attendance_utilisation": round(attendance_utilisation(actual, planned), 4),
                "cancellation_rate": round(
                    safe_divide(
                        sum(1 for row in service_bookings if _bool(row["cancellation_flag"])),
                        len(service_bookings),
                    ),
                    4,
                ),
                "no_show_rate": round(
                    safe_divide(
                        sum(1 for row in service_bookings if _bool(row["no_show_flag"])),
                        len(service_bookings),
                    ),
                    4,
                ),
                "contacts_per_occupied_hour": round(contacts_per_hour(completed, occupied), 4),
                "contacts_per_available_fte": round(
                    contacts_per_available_fte(completed, available_fte), 4
                ),
            }
        )
    return rows


def _room_service_metrics(
    bookings: list[dict[str, Any]], activity: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], dict[str, float | int | str]] = {}
    for booking in bookings:
        key = (str(booking["room_id"]), str(booking["service_id"]))
        row = grouped.setdefault(
            key,
            {
                "utilisation_run_id": "",
                "room_id": key[0],
                "service_id": key[1],
                "booked_hours": 0.0,
                "occupied_hours": 0.0,
                "completed_contacts": 0,
            },
        )
        if not _bool(booking["cancellation_flag"]):
            row["booked_hours"] = float(row["booked_hours"]) + _duration_hours(booking)
        if _occupied(booking):
            row["occupied_hours"] = float(row["occupied_hours"]) + _duration_hours(booking)
    for row in activity:
        key = (str(row["room_id"]), str(row["service_id"]))
        target = grouped.setdefault(
            key,
            {
                "utilisation_run_id": "",
                "room_id": key[0],
                "service_id": key[1],
                "booked_hours": 0.0,
                "occupied_hours": 0.0,
                "completed_contacts": 0,
            },
        )
        target["completed_contacts"] = int(target["completed_contacts"]) + int(
            row["completed_contacts"]
        )
    return [
        {
            **row,
            "booked_hours": round(float(row["booked_hours"]), 4),
            "occupied_hours": round(float(row["occupied_hours"]), 4),
        }
        for _, row in sorted(grouped.items())
    ]


def _time_band_metrics(
    bookings: list[dict[str, Any]], config: UtilisationConfig
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    for booking in bookings:
        booking_date = date.fromisoformat(str(booking["booking_date"]))
        values = {
            "weekday": weekdays[booking_date.weekday()],
            "time_band": assign_time_band(str(booking["start_time"]), config.time_bands),
        }
        for grain, value in values.items():
            key = (grain, value)
            row = grouped.setdefault(
                key,
                {
                    "utilisation_run_id": "",
                    "grain": grain,
                    "grain_value": value,
                    "booked_hours": 0.0,
                    "occupied_hours": 0.0,
                    "booking_count": 0,
                    "utilisation_value": 0.0,
                    "peak_flag": 0,
                },
            )
            if not _bool(booking["cancellation_flag"]):
                row["booked_hours"] += _duration_hours(booking)
            if _occupied(booking):
                row["occupied_hours"] += _duration_hours(booking)
            row["booking_count"] += 1
            row["peak_flag"] = (
                1 if grain == "time_band" and is_peak_band(value, config.time_bands) else 0
            )
    for row in grouped.values():
        row["booked_hours"] = round(float(row["booked_hours"]), 4)
        row["occupied_hours"] = round(float(row["occupied_hours"]), 4)
        row["utilisation_value"] = round(
            safe_divide(float(row["occupied_hours"]), float(row["booked_hours"])), 4
        )
    return [grouped[key] for key in sorted(grouped)]


def _monthly_metrics(
    rooms: list[dict[str, Any]],
    bookings: list[dict[str, Any]],
    start: date,
    end: date,
    config: UtilisationConfig,
) -> list[dict[str, Any]]:
    months = _month_keys(start, end)
    by_room_month: dict[tuple[str, str], dict[str, Any]] = {}
    for room in rooms:
        for month in months:
            by_room_month[(str(room["room_id"]), month)] = {
                "utilisation_run_id": "",
                "month": month,
                "room_id": room["room_id"],
                "available_hours": round(float(room["available_hours_per_week"]) * 52 / 12, 4),
                "booked_hours": 0.0,
                "occupied_hours": 0.0,
                "effective_utilisation": 0.0,
                "observation_count": 0,
            }
    for booking in bookings:
        month = str(booking["booking_date"])[:7]
        key = (str(booking["room_id"]), month)
        if key not in by_room_month:
            continue
        if not _bool(booking["cancellation_flag"]):
            by_room_month[key]["booked_hours"] += _duration_hours(booking)
        if _occupied(booking):
            by_room_month[key]["occupied_hours"] += _duration_hours(booking)
        by_room_month[key]["observation_count"] += 1
    for row in by_room_month.values():
        row["booked_hours"] = round(float(row["booked_hours"]), 4)
        row["occupied_hours"] = round(float(row["occupied_hours"]), 4)
        row["effective_utilisation"] = round(
            actual_occupied_utilisation(
                float(row["occupied_hours"]), float(row["available_hours"])
            ),
            4,
        )
    return [by_room_month[key] for key in sorted(by_room_month)]


def _underutilisation(
    room_rows: list[dict[str, Any]], monthly_rows: list[dict[str, Any]], config: UtilisationConfig
) -> list[dict[str, Any]]:
    monthly = _group(monthly_rows, "room_id")
    threshold = float(config.thresholds["persistent_under_utilisation"])
    minimum_below = int(config.thresholds["persistence_minimum_months_below_threshold"])
    minimum_observations = int(config.thresholds["minimum_observation_count"])
    rows = []
    for room in room_rows:
        room_months = monthly[str(room["room_id"])]
        observed = [row for row in room_months if int(row["observation_count"]) > 0]
        below = sum(1 for row in observed if float(row["effective_utilisation"]) < threshold)
        persistent = persistent_underutilisation_flag(
            below, len(observed), minimum_below, minimum_observations
        )
        protected = int(room["protected_capacity_flag"]) == 1
        rows.append(
            {
                "utilisation_run_id": "",
                "room_id": room["room_id"],
                "effective_utilisation": room["effective_utilisation"],
                "months_below_threshold": below,
                "observation_count": len(observed),
                "persistent_flag": 1 if persistent else 0,
                "protected_capacity_flag": 1 if protected else 0,
                "releasable_classification": "excluded_protected"
                if protected
                else "not_releasable_recommendation",
                "exclusion_reason": "protected_specialist_capacity" if protected else None,
            }
        )
    return rows


def _unit_costs(
    finance: list[dict[str, Any]],
    building_rows: list[dict[str, Any]],
    excluded_finance: set[str],
    connection: sqlite3.Connection,
    config: UtilisationConfig,
) -> list[dict[str, Any]]:
    included = tuple(config.cost_allocation["included_components"])
    finance_by_building = _group(finance, "building_id")
    excluded_buildings = {
        row["building_id"]
        for row in connection.execute("SELECT finance_record_id, building_id FROM curated_finance")
        if row["finance_record_id"] in excluded_finance
    }
    building_map = {str(row["building_id"]): row for row in building_rows}
    rows = []
    for building_id, building in sorted(building_map.items()):
        finance_rows = finance_by_building[building_id]
        annual_cost = (
            sum(annual_operating_cost(row, included) for row in finance_rows) / len(finance_rows)
            if finance_rows
            else 0.0
        )
        rows.append(
            {
                "utilisation_run_id": "",
                "building_id": building_id,
                "annual_operating_cost": round(annual_cost, 4),
                "cost_per_available_room_hour": round(
                    unit_cost(annual_cost, float(building["available_hours"])), 4
                ),
                "cost_per_booked_room_hour": round(
                    unit_cost(annual_cost, float(building["booked_hours"])), 4
                ),
                "cost_per_occupied_room_hour": round(
                    unit_cost(annual_cost, float(building["occupied_hours"])), 4
                ),
                "cost_per_completed_contact": round(
                    unit_cost(annual_cost, float(building["completed_contacts"])), 4
                ),
                "quality_flag": "manual_review_finance_excluded"
                if building_id in excluded_buildings
                else "none",
            }
        )
    return rows


def _summary(
    room_rows: list[dict[str, Any]], service_rows: list[dict[str, Any]]
) -> dict[str, float]:
    available = sum(float(row["available_hours"]) for row in room_rows)
    booked = sum(float(row["booked_hours"]) for row in room_rows)
    occupied = sum(float(row["occupied_hours"]) for row in room_rows)
    planned = sum(int(row["planned_attendance"]) for row in room_rows)
    actual = sum(int(row["actual_attendance"]) for row in room_rows)
    completed = sum(int(row["completed_contacts"]) for row in room_rows)
    total_bookings = sum(float(row["booked_hours"]) for row in service_rows)
    cancellation_rate = safe_divide(
        sum(float(row["cancellation_rate"]) for row in service_rows), len(service_rows)
    )
    no_show_rate = safe_divide(
        sum(float(row["no_show_rate"]) for row in service_rows), len(service_rows)
    )
    return {
        "available_hours": round(available, 4),
        "booked_hours": round(booked, 4),
        "occupied_hours": round(occupied, 4),
        "booked_utilisation": round(booked_utilisation(booked, available), 4),
        "actual_utilisation": round(actual_occupied_utilisation(occupied, available), 4),
        "attendance_utilisation": round(attendance_utilisation(actual, planned), 4),
        "effective_utilisation": round(
            safe_divide(
                sum(float(row["effective_utilisation"]) for row in room_rows), len(room_rows)
            ),
            4,
        ),
        "cancellation_rate": round(cancellation_rate, 4),
        "no_show_rate": round(no_show_rate, 4),
        "completed_contacts": float(completed),
        "contacts_per_occupied_room_hour": round(contacts_per_hour(completed, occupied), 4),
        "service_booked_hours_check": round(total_bookings, 4),
    }


def _insert_evidence(
    connection: sqlite3.Connection, utilisation_run_id: str, evidence: dict[str, Any]
) -> None:
    _insert_rows(
        connection, "evidence_analytics_population", evidence["population"], utilisation_run_id
    )
    _insert_rows(
        connection, "evidence_analytics_exclusions", evidence["exclusions"], utilisation_run_id
    )
    _insert_rows(connection, "evidence_room_utilisation", evidence["rooms"], utilisation_run_id)
    _insert_rows(
        connection, "evidence_building_utilisation", evidence["buildings"], utilisation_run_id
    )
    _insert_rows(connection, "evidence_site_utilisation", evidence["sites"], utilisation_run_id)
    _insert_rows(
        connection, "evidence_service_utilisation", evidence["services"], utilisation_run_id
    )
    _insert_rows(
        connection,
        "evidence_room_service_utilisation",
        evidence["room_services"],
        utilisation_run_id,
    )
    _insert_rows(
        connection, "evidence_time_band_utilisation", evidence["time_bands"], utilisation_run_id
    )
    _insert_rows(
        connection, "evidence_monthly_utilisation", evidence["monthly"], utilisation_run_id
    )
    _insert_rows(
        connection,
        "evidence_underutilisation_flags",
        evidence["underutilisation"],
        utilisation_run_id,
    )
    _insert_rows(connection, "evidence_unit_cost_metrics", evidence["costs"], utilisation_run_id)


def _insert_rows(
    connection: sqlite3.Connection, table: str, rows: list[dict[str, Any]], utilisation_run_id: str
) -> None:
    table_columns = {
        row["name"] for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
    }
    for row in rows:
        row = {
            key: value
            for key, value in {**row, "utilisation_run_id": utilisation_run_id}.items()
            if key in table_columns
        }
        columns = list(row)
        placeholders = ", ".join("?" for _ in columns)
        connection.execute(
            f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})",
            tuple(row[column] for column in columns),
        )


def _create_utilisation_tables(connection: sqlite3.Connection) -> None:
    connection.executescript(
        Path("database/schema/007_utilisation_tables.sql").read_text(encoding="utf-8")
    )


def _clear_utilisation_tables(connection: sqlite3.Connection) -> None:
    for table in (
        "evidence_utilisation_runs",
        "evidence_analytics_population",
        "evidence_analytics_exclusions",
        "evidence_room_utilisation",
        "evidence_building_utilisation",
        "evidence_site_utilisation",
        "evidence_service_utilisation",
        "evidence_room_service_utilisation",
        "evidence_time_band_utilisation",
        "evidence_monthly_utilisation",
        "evidence_underutilisation_flags",
        "evidence_unit_cost_metrics",
    ):
        connection.execute(f"DELETE FROM {table}")


def _utilisation_run_exists(connection: sqlite3.Connection, utilisation_run_id: str) -> bool:
    return (
        connection.execute(
            "SELECT utilisation_run_id FROM evidence_utilisation_runs WHERE utilisation_run_id = ?",
            (utilisation_run_id,),
        ).fetchone()
        is not None
    )


def _utilisation_run_id(*parts: str) -> str:
    digest = hashlib.sha256(json.dumps(parts, sort_keys=True).encode()).hexdigest()
    return f"UTL-{digest[:16]}"


def _formula_catalogue_checksum() -> str:
    payload = json.dumps(METRIC_CATALOGUE, sort_keys=True).encode()
    return hashlib.sha256(payload).hexdigest()


def _file_checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rows(connection: sqlite3.Connection, table: str) -> list[dict[str, Any]]:
    return [dict(row) for row in connection.execute(f"SELECT * FROM {table}")]


def _group(rows: list[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row[key])].append(row)
    return grouped


def _cascade(
    utilisation_run_id: str, dataset: str, record_identifier: str, reason: str
) -> dict[str, Any]:
    return {
        "utilisation_run_id": utilisation_run_id,
        "dataset": dataset,
        "record_identifier": record_identifier,
        "rule_id": None,
        "severity": None,
        "failure_action": None,
        "reason": reason,
        "analytical_effect": "record_removed_due_to_parent_exclusion",
    }


def _duration_hours(row: dict[str, Any]) -> float:
    return float(row["booked_duration_minutes"]) / 60


def _occupied(row: dict[str, Any]) -> bool:
    return (
        str(row["booking_status"]) == "completed"
        and not _bool(row["cancellation_flag"])
        and not _bool(row["no_show_flag"])
    )


def _bool(value: object) -> bool:
    return str(value).lower() == "true"


def _site_workforce_ratio(rows: list[dict[str, Any]]) -> float:
    available = sum(float(row["available_fte"]) for row in rows)
    planned = sum(float(row["planned_fte"]) for row in rows)
    return workforce_availability_ratio(available, planned)


def _month_keys(start: date, end: date) -> list[str]:
    keys = []
    current = date(start.year, start.month, 1)
    while current <= end:
        keys.append(f"{current.year:04d}-{current.month:02d}")
        current = date(
            current.year + (1 if current.month == 12 else 0),
            1 if current.month == 12 else current.month + 1,
            1,
        )
    return keys


def _round(value: float, config: UtilisationConfig) -> float:
    return round(value, int(config.rounding["decimal_places"]))
