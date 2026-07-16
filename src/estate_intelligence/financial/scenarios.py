"""Build financial cases from existing scenario and optimisation evidence."""

from __future__ import annotations

import sqlite3

from estate_intelligence.financial.models import FinanceConfig, FinancialCase


def build_financial_cases(
    connection: sqlite3.Connection, config: FinanceConfig
) -> list[FinancialCase]:
    active_buildings = _active_buildings(connection)
    cases: list[FinancialCase] = []
    for item in config.financial_case_catalogue:
        released: list[str] = []
        service_moves = 0
        remote_hours = 0.0
        release_supported = False
        statement = "baseline retains all recurring estate costs"
        if item.source_type == "scenario":
            service_moves = _scenario_service_moves(connection, item.source_case_id)
            statement = "heuristic scenario evidence does not support fixed building release"
        elif item.source_type == "optimisation":
            released = _optimisation_released_buildings(connection, item.source_case_id)
            service_moves = _optimisation_service_moves(connection, item.source_case_id)
            remote_hours = _optimisation_remote_hours(connection, item.source_case_id)
            release_supported = bool(released)
            statement = (
                "building release supported by optimisation building status"
                if release_supported
                else "optimisation evidence retains fixed building costs"
            )
        retained = sorted(building for building in active_buildings if building not in released)
        cases.append(
            FinancialCase(
                financial_case_id=item.financial_case_id,
                label=item.label,
                source_type=item.source_type,
                source_case_id=item.source_case_id,
                simulation_case_id=item.simulation_case_id,
                released_buildings=released,
                retained_buildings=retained,
                service_moves=service_moves,
                remote_demand_hours=remote_hours,
                release_supported=release_supported,
                release_statement=statement,
            )
        )
    return cases


def latest_building_costs(connection: sqlite3.Connection) -> dict[str, dict[str, float]]:
    year = connection.execute(
        """
        SELECT MAX(financial_year) AS year
        FROM curated_finance
        WHERE record_status LIKE 'accepted%'
        """
    ).fetchone()["year"]
    rows = connection.execute(
        """
        SELECT building_id, lease_cost, maintenance_cost, utility_cost, security_cost,
               cleaning_cost, business_rates, exit_cost
        FROM curated_finance
        WHERE financial_year = ? AND record_status LIKE 'accepted%'
        ORDER BY building_id
        """,
        (year,),
    ).fetchall()
    return {
        str(row["building_id"]): {
            "lease_cost": float(row["lease_cost"]),
            "maintenance_cost": float(row["maintenance_cost"]),
            "utility_cost": float(row["utility_cost"]),
            "security_cost": float(row["security_cost"]),
            "cleaning_cost": float(row["cleaning_cost"]),
            "business_rates": float(row["business_rates"]),
            "exit_cost": float(row["exit_cost"]),
        }
        for row in rows
    }


def _active_buildings(connection: sqlite3.Connection) -> set[str]:
    return {
        str(row["building_id"])
        for row in connection.execute(
            """
            SELECT DISTINCT building_id FROM curated_buildings
            WHERE record_status = 'accepted' AND active_flag = 'true'
            ORDER BY building_id
            """
        )
    }


def _optimisation_released_buildings(connection: sqlite3.Connection, case_id: str) -> list[str]:
    return [
        str(row["building_id"])
        for row in connection.execute(
            """
            SELECT building_id
            FROM evidence_optimisation_building_status
            WHERE case_id = ? AND active_value < 0.5 AND potentially_releasable_flag = 1
            ORDER BY building_id
            """,
            (case_id,),
        )
    ]


def _scenario_service_moves(connection: sqlite3.Connection, scenario_id: str) -> int:
    return int(
        connection.execute(
            "SELECT COUNT(*) AS count FROM evidence_scenario_service_moves WHERE scenario_id = ?",
            (scenario_id,),
        ).fetchone()["count"]
    )


def _optimisation_service_moves(connection: sqlite3.Connection, case_id: str) -> int:
    return int(
        connection.execute(
            "SELECT COUNT(*) AS count FROM evidence_optimisation_service_moves WHERE case_id = ?",
            (case_id,),
        ).fetchone()["count"]
    )


def _optimisation_remote_hours(connection: sqlite3.Connection, case_id: str) -> float:
    row = connection.execute(
        """
        SELECT SUM(remote_hours) AS hours
        FROM evidence_optimisation_allocations
        WHERE case_id = ?
        """,
        (case_id,),
    ).fetchone()
    return float(row["hours"] or 0.0)
