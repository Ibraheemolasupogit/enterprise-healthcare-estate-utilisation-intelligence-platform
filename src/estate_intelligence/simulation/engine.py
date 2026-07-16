"""Milestone 9 deterministic operational simulation engine."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections import defaultdict
from pathlib import Path
from statistics import mean, median
from typing import Any

from estate_intelligence.ingestion.database import connect
from estate_intelligence.simulation.arrivals import build_arrivals
from estate_intelligence.simulation.events import EventQueue
from estate_intelligence.simulation.experiments import configured_experiments, experiment_rows
from estate_intelligence.simulation.models import (
    AllocationInput,
    ContactEvent,
    ReplicationResult,
    RoomInput,
    ServiceInput,
    SimulationCase,
    SimulationConfig,
    SimulationEvidence,
    SimulationExperiment,
)
from estate_intelligence.simulation.reporting import export_simulation_evidence
from estate_intelligence.simulation.resources import RoomResource, WorkforceResource
from estate_intelligence.simulation.results import normal_ci, percentile, status_from_thresholds
from estate_intelligence.simulation.scenarios import (
    build_simulation_cases,
    load_rooms,
    load_services,
    load_workforce_capacity,
)
from estate_intelligence.simulation.seeds import SEED_STRATEGY_VERSION, random_stream, stable_seed
from estate_intelligence.simulation.service_times import sampled_duration
from estate_intelligence.simulation.validation import threshold_status

SIMULATION_TABLES = (
    "evidence_simulation_runs",
    "evidence_simulation_cases",
    "evidence_simulation_experiments",
    "evidence_simulation_replications",
    "evidence_simulation_events",
    "evidence_simulation_resource_metrics",
    "evidence_simulation_service_metrics",
    "evidence_simulation_queue_metrics",
    "evidence_simulation_workforce_metrics",
    "evidence_simulation_resilience_metrics",
    "evidence_simulation_threshold_results",
    "evidence_simulation_summary",
    "evidence_simulation_failures",
)


def run_simulation(
    *,
    database_path: Path,
    config_path: Path = Path("config/simulation.yaml"),
    output_dir: Path | None = None,
    rebuild: bool = False,
) -> dict[str, Any]:
    """Run deterministic operational simulation and persist evidence."""

    config = SimulationConfig.from_yaml(config_path)
    connection = connect(database_path)
    try:
        run_ids = _source_run_ids(connection)
        config_checksum = _file_checksum(config_path)
        rooms = load_rooms(connection)
        services = load_services(connection)
        workforce_capacity = load_workforce_capacity(connection)
        cases = build_simulation_cases(connection, config.allocation_sources)
        experiments = configured_experiments(config)
        experiment_checksum = _stable_checksum([item.model_dump() for item in experiments])
        allocation_checksum = _stable_checksum(_case_checksum_payload(cases))
        engine_identity = f"{config.engine}|{config.engine_version}|time_unit={config.time_unit}"
        simulation_run_id = _simulation_run_id(
            config.framework_version,
            run_ids["ingestion_run_id"],
            run_ids["quality_run_id"],
            run_ids["utilisation_run_id"],
            run_ids["forecast_run_id"],
            run_ids["scenario_run_id"],
            run_ids["optimisation_run_id"],
            config_checksum,
            experiment_checksum,
            allocation_checksum,
            SEED_STRATEGY_VERSION,
            engine_identity,
        )
        evidence = _run_all(
            simulation_run_id,
            config,
            cases,
            experiments,
            rooms,
            services,
            workforce_capacity,
        )
        readiness = _readiness(evidence.summary)
        with connection:
            _create_tables(connection)
            if rebuild:
                _clear_tables(connection)
            elif _run_exists(connection, simulation_run_id):
                raise FileExistsError(
                    "Refusing to overwrite existing simulation evidence without --rebuild"
                )
            _insert_rows(connection, "evidence_simulation_cases", evidence.cases)
            _insert_rows(connection, "evidence_simulation_experiments", evidence.experiments)
            _insert_rows(connection, "evidence_simulation_replications", evidence.replications)
            _insert_rows(connection, "evidence_simulation_events", evidence.events)
            _insert_rows(
                connection,
                "evidence_simulation_resource_metrics",
                evidence.resource_metrics,
            )
            _insert_rows(
                connection, "evidence_simulation_service_metrics", evidence.service_metrics
            )
            _insert_rows(connection, "evidence_simulation_queue_metrics", evidence.queue_metrics)
            _insert_rows(
                connection,
                "evidence_simulation_workforce_metrics",
                evidence.workforce_metrics,
            )
            _insert_rows(
                connection,
                "evidence_simulation_resilience_metrics",
                evidence.resilience_metrics,
            )
            _insert_rows(
                connection,
                "evidence_simulation_threshold_results",
                evidence.threshold_results,
            )
            _insert_rows(connection, "evidence_simulation_summary", evidence.summary)
            _insert_rows(connection, "evidence_simulation_failures", evidence.failures)
            connection.execute(
                """
                INSERT INTO evidence_simulation_runs
                (simulation_run_id, ingestion_run_id, quality_run_id, utilisation_run_id,
                 forecast_run_id, scenario_run_id, optimisation_run_id, framework_version,
                 config_checksum, experiment_catalogue_checksum, allocation_catalogue_checksum,
                 seed_strategy_version, simulation_engine_identity, master_seed, replications,
                 simulation_horizon, time_unit, readiness_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    simulation_run_id,
                    run_ids["ingestion_run_id"],
                    run_ids["quality_run_id"],
                    run_ids["utilisation_run_id"],
                    run_ids["forecast_run_id"],
                    run_ids["scenario_run_id"],
                    run_ids["optimisation_run_id"],
                    config.framework_version,
                    config_checksum,
                    experiment_checksum,
                    allocation_checksum,
                    SEED_STRATEGY_VERSION,
                    engine_identity,
                    config.master_seed,
                    config.replications,
                    config.simulation_horizon,
                    config.time_unit,
                    readiness,
                ),
            )
        exports: dict[str, str] = {}
        if output_dir is not None:
            exports = {
                name: str(path)
                for name, path in export_simulation_evidence(
                    connection, output_dir, simulation_run_id
                ).items()
            }
        return {
            "simulation_run_id": simulation_run_id,
            **run_ids,
            "config_checksum": config_checksum,
            "experiment_catalogue_checksum": experiment_checksum,
            "allocation_catalogue_checksum": allocation_checksum,
            "engine_identity": engine_identity,
            "case_count": len(cases),
            "experiment_count": len(experiments),
            "replications": config.replications,
            "readiness_status": readiness,
            "exports": exports,
        }
    finally:
        connection.close()


def verify_simulation(database_path: Path) -> dict[str, Any]:
    """Verify persisted simulation evidence."""

    connection = connect(database_path)
    try:
        run = connection.execute(
            "SELECT * FROM evidence_simulation_runs ORDER BY simulation_run_id LIMIT 1"
        ).fetchone()
        if run is None:
            raise ValueError("No simulation run evidence found")
        cases = connection.execute(
            "SELECT COUNT(*) AS count FROM evidence_simulation_cases"
        ).fetchone()["count"]
        experiments = connection.execute(
            "SELECT COUNT(*) AS count FROM evidence_simulation_experiments"
        ).fetchone()["count"]
        replications = connection.execute(
            "SELECT COUNT(*) AS count FROM evidence_simulation_replications"
        ).fetchone()["count"]
        summary = connection.execute(
            "SELECT COUNT(*) AS count FROM evidence_simulation_summary"
        ).fetchone()["count"]
        if cases != 4 or experiments != 6 or replications == 0 or summary != 24:
            raise ValueError("Simulation evidence is incomplete")
        return {
            "simulation_run_id": run["simulation_run_id"],
            "readiness_status": run["readiness_status"],
            "case_count": cases,
            "experiment_count": experiments,
            "replication_rows": replications,
            "summary_rows": summary,
        }
    finally:
        connection.close()


def export_existing_simulation_evidence(database_path: Path, output_dir: Path) -> dict[str, Path]:
    """Export persisted simulation evidence."""

    connection = connect(database_path)
    try:
        row = connection.execute(
            "SELECT simulation_run_id FROM evidence_simulation_runs "
            "ORDER BY simulation_run_id LIMIT 1"
        ).fetchone()
        if row is None:
            raise ValueError("No simulation run evidence found")
        return export_simulation_evidence(connection, output_dir, row["simulation_run_id"])
    finally:
        connection.close()


def _run_all(
    simulation_run_id: str,
    config: SimulationConfig,
    cases: list[SimulationCase],
    experiments: list[SimulationExperiment],
    rooms: dict[str, RoomInput],
    services: dict[str, ServiceInput],
    workforce_capacity: dict[str, float],
) -> SimulationEvidence:
    case_rows = [
        {
            "simulation_run_id": simulation_run_id,
            "simulation_case_id": case.simulation_case_id,
            "source_type": case.source_type,
            "source_case_id": case.source_case_id,
            "label": case.label,
            "active_rooms": case.active_rooms,
            "allocated_service_rooms": len({item.room_id for item in case.allocations}),
        }
        for case in cases
    ]
    replication_results: list[ReplicationResult] = []
    event_rows: list[dict[str, object]] = []
    for case in cases:
        for experiment in experiments:
            for replication in range(1, config.replications + 1):
                result = _simulate_replication(
                    simulation_run_id,
                    config,
                    case,
                    experiment,
                    replication,
                    rooms,
                    services,
                    workforce_capacity,
                )
                replication_results.append(result)
                if replication == 1:
                    event_rows.extend(
                        _event_rows(
                            simulation_run_id,
                            case.simulation_case_id,
                            experiment.experiment_id,
                            replication,
                            result.events[:10],
                        )
                    )
    return _aggregate_evidence(
        simulation_run_id,
        config,
        case_rows,
        experiment_rows(simulation_run_id, experiments),
        replication_results,
        event_rows,
    )


def _simulate_replication(
    simulation_run_id: str,
    config: SimulationConfig,
    case: SimulationCase,
    experiment: SimulationExperiment,
    replication: int,
    rooms: dict[str, RoomInput],
    services: dict[str, ServiceInput],
    workforce_capacity: dict[str, float],
) -> ReplicationResult:
    del simulation_run_id
    rep_seed = stable_seed(
        config.master_seed, case.simulation_case_id, experiment.experiment_id, replication
    )
    stream_parts = (case.simulation_case_id, experiment.experiment_id, replication)
    arrivals = build_arrivals(
        config=config,
        allocations=case.allocations,
        services=services,
        demand_multiplier=experiment.demand_multiplier,
        duration_multiplier=experiment.duration_multiplier,
        lateness_rng=random_stream(config.master_seed, *stream_parts, "lateness"),
        cancellation_rng=random_stream(config.master_seed, *stream_parts, "cancellation"),
        no_show_rng=random_stream(config.master_seed, *stream_parts, "no_show"),
        duration_rng=random_stream(config.master_seed, *stream_parts, "duration"),
        duration_fn=sampled_duration,
    )
    room_resources = {
        room_id: RoomResource(_adjust_room(rooms[room_id], experiment))
        for room_id in sorted(case.active_room_ids)
        if room_id in rooms
    }
    service_capacity = _service_capacity(config, case.allocations, workforce_capacity, experiment)
    workforce = {
        service_id: WorkforceResource(service_id, capacity)
        for service_id, capacity in sorted(service_capacity.items())
    }
    queue = EventQueue()
    for arrival in arrivals:
        queue.schedule(arrival.arrival_minute, "arrival", {"arrival": arrival})
    events: list[ContactEvent] = []
    service_waits: dict[str, list[float]] = defaultdict(list)
    service_arrivals: dict[str, int] = defaultdict(int)
    service_completed: dict[str, int] = defaultdict(int)
    service_unserved: dict[str, int] = defaultdict(int)
    room_waits: dict[tuple[str, str], list[float]] = defaultdict(list)
    while queue:
        scheduled = queue.pop()
        arrival = scheduled.payload["arrival"]
        service_arrivals[arrival.service_id] += 1
        if arrival.cancelled or arrival.no_show:
            status = "cancelled" if arrival.cancelled else "no_show"
            service_unserved[arrival.service_id] += 1
            events.append(
                ContactEvent(
                    sequence=arrival.sequence,
                    event_type="arrival",
                    event_time=arrival.arrival_minute,
                    service_id=arrival.service_id,
                    room_id=arrival.room_id,
                    wait_minutes=0.0,
                    service_duration_minutes=0.0,
                    completion_status=status,
                )
            )
            continue
        worker = workforce.setdefault(arrival.service_id, WorkforceResource(arrival.service_id, 1))
        if not worker.request() or arrival.room_id not in room_resources:
            service_unserved[arrival.service_id] += 1
            events.append(
                ContactEvent(
                    sequence=arrival.sequence,
                    event_type="arrival",
                    event_time=arrival.arrival_minute,
                    service_id=arrival.service_id,
                    room_id=arrival.room_id,
                    wait_minutes=0.0,
                    service_duration_minutes=0.0,
                    completion_status="workforce_blocked",
                )
            )
            continue
        day_start = int(arrival.arrival_minute // 1440) * 1440
        start, finish = room_resources[arrival.room_id].assign(
            arrival, float(day_start), arrival.duration_minutes
        )
        wait = start - arrival.arrival_minute
        service_waits[arrival.service_id].append(wait)
        room_waits[(arrival.service_id, arrival.room_id)].append(wait)
        service_completed[arrival.service_id] += 1
        events.append(
            ContactEvent(
                sequence=arrival.sequence,
                event_type="completion",
                event_time=finish,
                service_id=arrival.service_id,
                room_id=arrival.room_id,
                wait_minutes=wait,
                service_duration_minutes=arrival.duration_minutes,
                completion_status="completed",
            )
        )
    wait_values = [event.wait_minutes for event in events if event.completion_status == "completed"]
    completed = sum(service_completed.values())
    unserved = sum(service_unserved.values())
    status = "pass" if unserved == 0 else "review_required"
    return ReplicationResult(
        simulation_case_id=case.simulation_case_id,
        experiment_id=experiment.experiment_id,
        replication=replication,
        replication_seed=rep_seed,
        events=sorted(events, key=lambda item: (item.event_time, item.sequence)),
        room_rows=_room_rows(case, experiment, room_resources, config),
        service_rows=_service_rows(
            config, service_arrivals, service_completed, service_unserved, service_waits
        ),
        queue_rows=_queue_rows(case, experiment, room_waits, room_resources),
        workforce_rows=_workforce_rows(workforce),
        arrivals=len(arrivals),
        completed_contacts=completed,
        unserved_contacts=unserved,
        completion_rate=completed / len(arrivals) if arrivals else 1.0,
        mean_wait_minutes=mean(wait_values) if wait_values else 0.0,
        p95_wait_minutes=percentile(wait_values, 0.95),
        room_contention_events=sum(room.contention_events for room in room_resources.values()),
        workforce_blocked_contacts=sum(worker.blocked_contacts for worker in workforce.values()),
        status=status,
    )


def _aggregate_evidence(
    simulation_run_id: str,
    config: SimulationConfig,
    case_rows: list[dict[str, object]],
    experiment_rows_payload: list[dict[str, object]],
    results: list[ReplicationResult],
    event_rows: list[dict[str, object]],
) -> SimulationEvidence:
    rep_rows = [_replication_row(simulation_run_id, result) for result in results]
    grouped: dict[tuple[str, str], list[ReplicationResult]] = defaultdict(list)
    for result in results:
        grouped[(result.simulation_case_id, result.experiment_id)].append(result)
    resource_rows = _aggregate_named_rows(simulation_run_id, results, "room_rows", ("room_id",))
    service_rows = _aggregate_named_rows(
        simulation_run_id, results, "service_rows", ("service_id",)
    )
    queue_rows = _aggregate_named_rows(
        simulation_run_id, results, "queue_rows", ("service_id", "room_id")
    )
    workforce_rows = _aggregate_named_rows(
        simulation_run_id, results, "workforce_rows", ("service_id",)
    )
    resilience_rows: list[dict[str, object]] = []
    threshold_rows: list[dict[str, object]] = []
    summary_rows: list[dict[str, object]] = []
    failure_rows: list[dict[str, object]] = []
    for (case_id, experiment_id), values in sorted(grouped.items()):
        resilience, thresholds, failures = _resilience_rows(
            simulation_run_id, config, case_id, experiment_id, values
        )
        resilience_rows.append(resilience)
        threshold_rows.extend(thresholds)
        failure_rows.extend(failures)
        summary_rows.append(_summary_row(simulation_run_id, resilience, values))
    return SimulationEvidence(
        cases=case_rows,
        experiments=experiment_rows_payload,
        replications=rep_rows,
        events=event_rows,
        resource_metrics=resource_rows,
        service_metrics=service_rows,
        queue_metrics=queue_rows,
        workforce_metrics=workforce_rows,
        resilience_metrics=resilience_rows,
        threshold_results=threshold_rows,
        summary=summary_rows,
        failures=failure_rows,
    )


def _resilience_rows(
    simulation_run_id: str,
    config: SimulationConfig,
    case_id: str,
    experiment_id: str,
    results: list[ReplicationResult],
) -> tuple[dict[str, object], list[dict[str, object]], list[dict[str, object]]]:
    thresholds = config.performance_thresholds
    arrivals = round(mean([result.arrivals for result in results]))
    completed = round(mean([result.completed_contacts for result in results]))
    unserved = round(mean([result.unserved_contacts for result in results]))
    completion_rates = [result.completion_rate for result in results]
    mean_waits = [result.mean_wait_minutes for result in results]
    p95_wait = mean([result.p95_wait_minutes for result in results])
    max_wait = max(
        (max((event.wait_minutes for event in result.events), default=0.0) for result in results),
        default=0.0,
    )
    room_occupancy = mean([_max_room_occupancy(result.room_rows) for result in results])
    overtime = mean(
        [sum(_as_float(row["overtime_minutes"]) for row in result.room_rows) for result in results]
    )
    contingency_remaining = max(0.0, 1.0 - room_occupancy)
    contingency_consumed = max(
        0.0, float(config.contingency_policy["planned_idle_fraction"]) - contingency_remaining
    )
    completion_ci = normal_ci(completion_rates, float(config.confidence_interval["level"]))
    wait_ci = normal_ci(mean_waits, float(config.confidence_interval["level"]))
    observed = {
        "maximum_mean_wait_minutes": mean(mean_waits) if mean_waits else 0.0,
        "maximum_p95_wait_minutes": p95_wait,
        "minimum_completion_rate": mean(completion_rates) if completion_rates else 1.0,
        "maximum_room_occupancy": room_occupancy,
        "maximum_overtime_minutes": overtime,
        "maximum_unserved_contacts": float(unserved),
        "minimum_contingency_remaining": contingency_remaining,
    }
    threshold_rows = []
    failure_rows = []
    failures = 0
    for index, (name, observed_value) in enumerate(sorted(observed.items()), start=1):
        threshold_value = float(thresholds[name])
        status = threshold_status(name, observed_value, threshold_value)
        failures += 1 if status == "fail" else 0
        threshold_rows.append(
            {
                "simulation_run_id": simulation_run_id,
                "simulation_case_id": case_id,
                "experiment_id": experiment_id,
                "threshold_name": name,
                "threshold_value": round(threshold_value, 4),
                "observed_value": round(observed_value, 4),
                "result_status": status,
            }
        )
        if status == "fail":
            failure_rows.append(
                {
                    "simulation_run_id": simulation_run_id,
                    "simulation_case_id": case_id,
                    "experiment_id": experiment_id,
                    "failure_id": f"SIMFAIL-{index:03d}",
                    "failure_type": name,
                    "entity_id": f"{case_id}__{experiment_id}",
                    "observed_value": round(observed_value, 4),
                    "threshold_value": round(threshold_value, 4),
                    "detail": f"{name} breached configured simulation threshold",
                }
            )
    status = status_from_thresholds(failures)
    return (
        {
            "simulation_run_id": simulation_run_id,
            "simulation_case_id": case_id,
            "experiment_id": experiment_id,
            "arrivals": arrivals,
            "completed_contacts": completed,
            "completion_rate": round(mean(completion_rates), 4) if completion_rates else 1.0,
            "mean_wait_minutes": round(mean(mean_waits), 4) if mean_waits else 0.0,
            "p95_wait_minutes": round(p95_wait, 4),
            "max_wait_minutes": round(max_wait, 4),
            "room_occupancy": round(room_occupancy, 4),
            "overtime_minutes": round(overtime, 4),
            "unserved_contacts": unserved,
            "contingency_consumed": round(contingency_consumed, 4),
            "contingency_remaining": round(contingency_remaining, 4),
            "threshold_failure_frequency": round(
                sum(1 for result in results if result.status != "pass") / len(results), 4
            ),
            "ci_method": str(config.confidence_interval["method"]),
            "ci_level": float(config.confidence_interval["level"]),
            "completion_rate_ci_low": round(completion_ci[0], 4),
            "completion_rate_ci_high": round(completion_ci[1], 4),
            "mean_wait_ci_low": round(wait_ci[0], 4),
            "mean_wait_ci_high": round(wait_ci[1], 4),
            "status": status,
        },
        threshold_rows,
        failure_rows,
    )


def _summary_row(
    simulation_run_id: str,
    resilience: dict[str, object],
    results: list[ReplicationResult],
) -> dict[str, object]:
    workforce_bottlenecks = round(mean([result.workforce_blocked_contacts for result in results]))
    status = str(resilience["status"])
    return {
        "simulation_run_id": simulation_run_id,
        "simulation_case_id": resilience["simulation_case_id"],
        "experiment_id": resilience["experiment_id"],
        "status": status,
        "arrivals": resilience["arrivals"],
        "completed_contacts": resilience["completed_contacts"],
        "unserved_contacts": resilience["unserved_contacts"],
        "completion_rate": resilience["completion_rate"],
        "mean_wait_minutes": resilience["mean_wait_minutes"],
        "p95_wait_minutes": resilience["p95_wait_minutes"],
        "room_occupancy": resilience["room_occupancy"],
        "overtime_minutes": resilience["overtime_minutes"],
        "workforce_bottleneck_count": workforce_bottlenecks,
        "comparison_statement": (
            "Simulation evidence tests operational resilience; it is not a final recommendation."
        ),
    }


def _aggregate_named_rows(
    simulation_run_id: str,
    results: list[ReplicationResult],
    attr: str,
    id_columns: tuple[str, ...],
) -> list[dict[str, object]]:
    grouped: dict[tuple[object, ...], list[dict[str, object]]] = defaultdict(list)
    for result in results:
        for row in getattr(result, attr):
            key = (
                result.simulation_case_id,
                result.experiment_id,
                *(row[column] for column in id_columns),
            )
            grouped[key].append(row)
    output = []
    for key, rows in sorted(grouped.items()):
        case_id = str(key[0])
        experiment_id = str(key[1])
        base: dict[str, object] = {
            "simulation_run_id": simulation_run_id,
            "simulation_case_id": case_id,
            "experiment_id": experiment_id,
        }
        first = rows[0]
        for column in id_columns:
            base[column] = first[column]
        for column, value in first.items():
            if column in id_columns:
                continue
            if isinstance(value, int | float):
                base[column] = round(mean(_as_float(row[column]) for row in rows), 4)
            else:
                base[column] = value
        output.append(base)
    return output


def _replication_row(simulation_run_id: str, result: ReplicationResult) -> dict[str, object]:
    return {
        "simulation_run_id": simulation_run_id,
        "simulation_case_id": result.simulation_case_id,
        "experiment_id": result.experiment_id,
        "replication": result.replication,
        "replication_seed": result.replication_seed,
        "arrivals": result.arrivals,
        "completed_contacts": result.completed_contacts,
        "unserved_contacts": result.unserved_contacts,
        "completion_rate": round(result.completion_rate, 4),
        "mean_wait_minutes": round(result.mean_wait_minutes, 4),
        "p95_wait_minutes": round(result.p95_wait_minutes, 4),
        "room_contention_events": result.room_contention_events,
        "workforce_blocked_contacts": result.workforce_blocked_contacts,
        "status": result.status,
    }


def _event_rows(
    simulation_run_id: str,
    case_id: str,
    experiment_id: str,
    replication: int,
    events: list[ContactEvent],
) -> list[dict[str, object]]:
    return [
        {
            "simulation_run_id": simulation_run_id,
            "simulation_case_id": case_id,
            "experiment_id": experiment_id,
            "replication": replication,
            "event_sequence": index,
            "event_type": event.event_type,
            "event_time": round(event.event_time, 4),
            "service_id": event.service_id,
            "room_id": event.room_id,
            "wait_minutes": round(event.wait_minutes, 4),
            "service_duration_minutes": round(event.service_duration_minutes, 4),
            "completion_status": event.completion_status,
        }
        for index, event in enumerate(events, start=1)
    ]


def _room_rows(
    case: SimulationCase,
    experiment: SimulationExperiment,
    rooms: dict[str, RoomResource],
    config: SimulationConfig,
) -> list[dict[str, object]]:
    del case, experiment
    horizon_minutes = config.simulation_horizon * 24 * 60
    rows: list[dict[str, object]] = []
    for resource in rooms.values():
        available = (
            resource.room.closing_minute - resource.room.opening_minute
        ) * config.simulation_horizon
        busy = min(resource.busy_minutes, horizon_minutes)
        rows.append(
            {
                "room_id": resource.room.room_id,
                "building_id": resource.room.building_id,
                "site_id": resource.room.site_id,
                "room_type": resource.room.room_type,
                "protected_capacity_flag": 1 if resource.room.protected_capacity_flag else 0,
                "specialist_flag": 1 if resource.room.specialist_flag else 0,
                "busy_minutes": round(busy, 4),
                "idle_minutes": round(max(0.0, available - busy), 4),
                "occupancy_rate": round(busy / available if available else 0.0, 4),
                "overtime_minutes": round(resource.overtime_minutes, 4),
                "contention_events": resource.contention_events,
                "peak_queue_length": resource.peak_queue_length,
                "capacity_breaches": resource.capacity_breaches,
            }
        )
    return rows


def _service_rows(
    config: SimulationConfig,
    arrivals: dict[str, int],
    completed: dict[str, int],
    unserved: dict[str, int],
    waits: dict[str, list[float]],
) -> list[dict[str, object]]:
    rows = []
    wait_threshold = float(config.performance_thresholds["maximum_mean_wait_minutes"])
    for service_id in sorted(set(arrivals) | set(completed) | set(unserved)):
        service_waits = waits.get(service_id, [])
        total = arrivals.get(service_id, 0)
        done = completed.get(service_id, 0)
        missed = unserved.get(service_id, 0)
        rows.append(
            {
                "service_id": service_id,
                "arrivals": total,
                "completed_contacts": done,
                "unserved_contacts": missed,
                "completion_rate": round(done / total if total else 1.0, 4),
                "mean_wait_minutes": round(mean(service_waits), 4) if service_waits else 0.0,
                "median_wait_minutes": round(median(service_waits), 4) if service_waits else 0.0,
                "p90_wait_minutes": round(percentile(service_waits, 0.90), 4),
                "p95_wait_minutes": round(percentile(service_waits, 0.95), 4),
                "max_wait_minutes": round(max(service_waits, default=0.0), 4),
                "delayed_session_count": sum(1 for wait in service_waits if wait > wait_threshold),
                "threshold_exceedance_rate": round(
                    sum(1 for wait in service_waits if wait > wait_threshold) / len(service_waits)
                    if service_waits
                    else 0.0,
                    4,
                ),
                "session_overrun_minutes": 0.0,
                "unmet_simulated_demand": missed,
                "status": "pass" if missed == 0 else "review_required",
            }
        )
    return rows


def _queue_rows(
    case: SimulationCase,
    experiment: SimulationExperiment,
    waits: dict[tuple[str, str], list[float]],
    rooms: dict[str, RoomResource],
) -> list[dict[str, object]]:
    del case, experiment
    rows = []
    for (service_id, room_id), values in sorted(waits.items()):
        room = rooms[room_id]
        rows.append(
            {
                "service_id": service_id,
                "room_id": room_id,
                "mean_queue_length": round(room.contention_events / max(len(values), 1), 4),
                "peak_queue_length": room.peak_queue_length,
                "contention_events": room.contention_events,
                "mean_wait_minutes": round(mean(values), 4) if values else 0.0,
                "p95_wait_minutes": round(percentile(values, 0.95), 4),
            }
        )
    return rows


def _workforce_rows(workforce: dict[str, WorkforceResource]) -> list[dict[str, object]]:
    return [
        {
            "service_id": worker.service_id,
            "available_contact_slots": float(worker.capacity_contacts),
            "used_contact_slots": float(worker.used_contacts),
            "workforce_utilisation": round(
                worker.used_contacts / worker.capacity_contacts
                if worker.capacity_contacts
                else 0.0,
                4,
            ),
            "blocked_demand_contacts": worker.blocked_contacts,
            "overtime_minutes": 0.0,
            "workforce_bottleneck_count": 1 if worker.blocked_contacts > 0 else 0,
        }
        for worker in sorted(workforce.values(), key=lambda item: item.service_id)
    ]


def _service_capacity(
    config: SimulationConfig,
    allocations: list[AllocationInput],
    workforce_capacity: dict[str, float],
    experiment: SimulationExperiment,
) -> dict[str, int]:
    services = {allocation.service_id for allocation in allocations}
    scale = config.simulation_horizon / config.working_days_per_month
    minimum = int(config.workforce_availability["minimum_daily_contacts"])
    return {
        service_id: max(
            minimum,
            round(
                workforce_capacity.get(service_id, float(minimum))
                * scale
                * experiment.workforce_multiplier
            ),
        )
        for service_id in services
    }


def _adjust_room(room: RoomInput, experiment: SimulationExperiment) -> RoomInput:
    if not room.specialist_flag:
        return room
    available = room.closing_minute - room.opening_minute
    adjusted_close = room.opening_minute + round(
        available * experiment.specialist_room_capacity_multiplier
    )
    return room.model_copy(update={"closing_minute": adjusted_close})


def _max_room_occupancy(rows: list[dict[str, object]]) -> float:
    if not rows:
        return 0.0
    return max(_as_float(row["occupancy_rate"]) for row in rows)


def _readiness(summary_rows: list[dict[str, object]]) -> str:
    statuses = {str(row["status"]) for row in summary_rows}
    if statuses == {"pass"}:
        return "simulation_evidence_ready"
    if "fail" in statuses:
        return "review_required"
    return "pass_with_warnings"


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


def _create_tables(connection: sqlite3.Connection) -> None:
    connection.executescript(
        Path("database/schema/011_simulation_tables.sql").read_text(encoding="utf-8")
    )


def _clear_tables(connection: sqlite3.Connection) -> None:
    for table in SIMULATION_TABLES:
        connection.execute(f"DELETE FROM {table}")


def _run_exists(connection: sqlite3.Connection, simulation_run_id: str) -> bool:
    return (
        connection.execute(
            "SELECT simulation_run_id FROM evidence_simulation_runs WHERE simulation_run_id = ?",
            (simulation_run_id,),
        ).fetchone()
        is not None
    )


def _source_run_ids(connection: sqlite3.Connection) -> dict[str, str]:
    queries = {
        "ingestion_run_id": (
            "SELECT ingestion_run_id AS id "
            "FROM evidence_ingestion_runs ORDER BY ingestion_run_id LIMIT 1"
        ),
        "quality_run_id": (
            "SELECT quality_run_id AS id FROM evidence_quality_runs ORDER BY quality_run_id LIMIT 1"
        ),
        "utilisation_run_id": (
            "SELECT utilisation_run_id AS id "
            "FROM evidence_utilisation_runs ORDER BY utilisation_run_id LIMIT 1"
        ),
        "forecast_run_id": (
            "SELECT forecast_run_id AS id "
            "FROM evidence_forecast_runs ORDER BY forecast_run_id LIMIT 1"
        ),
        "scenario_run_id": (
            "SELECT scenario_run_id AS id "
            "FROM evidence_scenario_runs ORDER BY scenario_run_id LIMIT 1"
        ),
        "optimisation_run_id": (
            "SELECT optimisation_run_id AS id "
            "FROM evidence_optimisation_runs ORDER BY optimisation_run_id LIMIT 1"
        ),
    }
    result = {}
    for key, query in queries.items():
        row = connection.execute(query).fetchone()
        if row is None:
            raise ValueError(
                "Completed upstream ingestion through optimisation evidence is required"
            )
        result[key] = str(row["id"])
    return result


def _simulation_run_id(*parts: str) -> str:
    digest = hashlib.sha256(json.dumps(parts, sort_keys=True).encode()).hexdigest()
    return f"SIM-{digest[:16]}"


def _case_checksum_payload(cases: list[SimulationCase]) -> list[dict[str, Any]]:
    payload: list[dict[str, Any]] = []
    for case in sorted(cases, key=lambda item: item.simulation_case_id):
        allocations = sorted(
            [allocation.model_dump(mode="json") for allocation in case.allocations],
            key=lambda item: (
                item["service_id"],
                item["period"],
                item["room_id"],
                item["building_id"],
                item["site_id"],
            ),
        )
        payload.append(
            {
                "simulation_case_id": case.simulation_case_id,
                "source_type": case.source_type,
                "source_case_id": case.source_case_id,
                "label": case.label,
                "allocations": allocations,
                "active_room_ids": sorted(case.active_room_ids),
            }
        )
    return payload


def _file_checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _stable_checksum(payload: object) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def _as_float(value: object) -> float:
    if isinstance(value, int | float | str):
        return float(value)
    raise TypeError(f"Expected numeric simulation value, got {type(value)}")
