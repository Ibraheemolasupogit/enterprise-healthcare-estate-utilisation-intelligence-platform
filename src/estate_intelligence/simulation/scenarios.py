"""Build simulation cases from scenario and optimisation evidence."""

from __future__ import annotations

import sqlite3

from estate_intelligence.simulation.models import (
    AllocationInput,
    RoomInput,
    ServiceInput,
    SimulationCase,
)


def load_rooms(connection: sqlite3.Connection) -> dict[str, RoomInput]:
    rows = connection.execute(
        """
        SELECT r.room_id, r.building_id, b.site_id, r.room_type, r.capacity,
               COALESCE(r.specialist_equipment, '') AS specialist_equipment,
               r.protected_capacity_flag, r.opening_time, r.closing_time
        FROM curated_rooms r
        JOIN curated_buildings b ON b.building_id = r.building_id
        WHERE r.record_status = 'accepted' AND r.active_flag = 'true'
        ORDER BY r.room_id
        """
    ).fetchall()
    return {
        str(row["room_id"]): RoomInput(
            room_id=str(row["room_id"]),
            building_id=str(row["building_id"]),
            site_id=str(row["site_id"]),
            room_type=str(row["room_type"]),
            capacity=int(float(row["capacity"])),
            specialist_equipment=str(row["specialist_equipment"] or ""),
            protected_capacity_flag=str(row["protected_capacity_flag"]).lower() == "true",
            specialist_flag=bool(str(row["specialist_equipment"] or "")),
            opening_minute=_time_to_minute(str(row["opening_time"])),
            closing_minute=_time_to_minute(str(row["closing_time"])),
        )
        for row in rows
    }


def load_services(connection: sqlite3.Connection) -> dict[str, ServiceInput]:
    duration_rows = connection.execute(
        """
        SELECT service_id, AVG(average_contact_duration_minutes) AS avg_minutes
        FROM curated_clinical_activity
        WHERE record_status = 'accepted'
        GROUP BY service_id
        """
    ).fetchall()
    durations = {str(row["service_id"]): float(row["avg_minutes"] or 30.0) for row in duration_rows}
    rows = connection.execute(
        """
        SELECT service_id, service_name, minimum_room_type,
               COALESCE(specialist_equipment_required, '') AS specialist_equipment_required,
               remote_eligible_rate
        FROM curated_services
        WHERE record_status = 'accepted' AND active_flag = 'true'
        ORDER BY service_id
        """
    ).fetchall()
    return {
        str(row["service_id"]): ServiceInput(
            service_id=str(row["service_id"]),
            service_name=str(row["service_name"]),
            minimum_room_type=str(row["minimum_room_type"]),
            specialist_equipment_required=str(row["specialist_equipment_required"] or ""),
            remote_eligible_rate=float(row["remote_eligible_rate"] or 0.0),
            average_duration_minutes=max(5.0, durations.get(str(row["service_id"]), 30.0)),
        )
        for row in rows
    }


def build_simulation_cases(
    connection: sqlite3.Connection,
    allocation_sources: dict[str, str],
) -> list[SimulationCase]:
    baseline_case = allocation_sources["baseline_case_id"]
    light_scenario = allocation_sources["light_consolidation_scenario_id"]
    flexible_case = allocation_sources["flexible_room_optimisation_case_id"]
    hybrid_case = allocation_sources["hybrid_optimisation_case_id"]
    cases = [
        SimulationCase(
            simulation_case_id="case_a_current_estate",
            source_type="optimisation",
            source_case_id=baseline_case,
            label="Case A: Current-estate baseline",
            allocations=_optimisation_allocations(connection, baseline_case, None),
            active_room_ids=_active_optimisation_rooms(connection, baseline_case),
        ),
        SimulationCase(
            simulation_case_id="case_b_light_consolidation",
            source_type="scenario",
            source_case_id=light_scenario,
            label="Case B: Milestone 7 light-consolidation scenario",
            allocations=_optimisation_allocations(
                connection,
                baseline_case,
                _retained_scenario_rooms(connection, light_scenario),
            ),
            active_room_ids=_retained_scenario_rooms(connection, light_scenario),
        ),
        SimulationCase(
            simulation_case_id="case_c_flexible_room_optimisation",
            source_type="optimisation",
            source_case_id=flexible_case,
            label="Case C: Milestone 8 flexible-room optimisation",
            allocations=_optimisation_allocations(connection, flexible_case, None),
            active_room_ids=_active_optimisation_rooms(connection, flexible_case),
        ),
        SimulationCase(
            simulation_case_id="case_d_hybrid_optimisation",
            source_type="optimisation",
            source_case_id=hybrid_case,
            label="Case D: Milestone 8 hybrid optimisation",
            allocations=_optimisation_allocations(connection, hybrid_case, None),
            active_room_ids=_active_optimisation_rooms(connection, hybrid_case),
        ),
    ]
    return cases


def load_workforce_capacity(connection: sqlite3.Connection) -> dict[str, float]:
    rows = connection.execute(
        """
        SELECT entity_id AS service_id, AVG(forecast_value) AS capacity
        FROM evidence_forecast_values
        WHERE target = 'session_capacity_by_service'
          AND value_type = 'future_forecast'
        GROUP BY entity_id
        """
    ).fetchall()
    if not rows:
        rows = connection.execute(
            """
            SELECT service_id, AVG(session_capacity) AS capacity
            FROM curated_workforce
            WHERE record_status = 'accepted'
            GROUP BY service_id
            """
        ).fetchall()
    return {str(row["service_id"]): float(row["capacity"] or 1.0) for row in rows}


def _optimisation_allocations(
    connection: sqlite3.Connection,
    case_id: str,
    room_filter: set[str] | None,
) -> list[AllocationInput]:
    rows = connection.execute(
        """
        SELECT case_id, service_id, period, room_id, building_id, site_id,
               allocated_hours, remote_hours
        FROM evidence_optimisation_allocations
        WHERE case_id = ? AND allocated_hours > 0
        ORDER BY service_id, period, room_id
        """,
        (case_id,),
    ).fetchall()
    allocations = []
    for row in rows:
        room_id = str(row["room_id"])
        if room_filter is not None and room_id not in room_filter:
            continue
        allocations.append(
            AllocationInput(
                simulation_case_id=case_id,
                service_id=str(row["service_id"]),
                period=str(row["period"]),
                room_id=room_id,
                building_id=str(row["building_id"]),
                site_id=str(row["site_id"]),
                allocated_hours=float(row["allocated_hours"]),
                remote_hours=float(row["remote_hours"]),
            )
        )
    return allocations


def _active_optimisation_rooms(connection: sqlite3.Connection, case_id: str) -> set[str]:
    return {
        str(row["room_id"])
        for row in connection.execute(
            """
            SELECT room_id FROM evidence_optimisation_room_status
            WHERE case_id = ? AND active_value >= 0.5
            ORDER BY room_id
            """,
            (case_id,),
        )
    }


def _retained_scenario_rooms(connection: sqlite3.Connection, scenario_id: str) -> set[str]:
    return {
        str(row["room_id"])
        for row in connection.execute(
            """
            SELECT room_id FROM evidence_scenario_room_actions
            WHERE scenario_id = ? AND action = 'retain'
            ORDER BY room_id
            """,
            (scenario_id,),
        )
    }


def _time_to_minute(value: str) -> int:
    hour, minute = value.split(":")
    return int(hour) * 60 + int(minute)
