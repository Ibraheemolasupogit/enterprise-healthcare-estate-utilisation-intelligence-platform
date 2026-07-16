"""Milestone 10 deterministic financial analysis engine."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

from estate_intelligence.financial.assumptions import assumption_rows
from estate_intelligence.financial.break_even import (
    maximum_mitigation_before_negative,
    maximum_transition_cost_for_zero_npv,
    minimum_annual_effect_for_payback,
)
from estate_intelligence.financial.cashflows import annual_cashflows
from estate_intelligence.financial.costs import (
    recurring_cost_rows,
    total_amount,
    transition_cost_rows,
)
from estate_intelligence.financial.models import (
    AssumptionSetConfig,
    FinanceConfig,
    FinanceEvidence,
    FinancialCase,
)
from estate_intelligence.financial.npv import net_present_value
from estate_intelligence.financial.payback import payback_year
from estate_intelligence.financial.reporting import export_financial_evidence
from estate_intelligence.financial.risk_adjustment import (
    confidence_status,
    readiness_status,
    realisability_cap,
)
from estate_intelligence.financial.scenarios import (
    build_financial_cases,
    latest_building_costs,
)
from estate_intelligence.financial.sensitivity import sensitivity_rows
from estate_intelligence.ingestion.database import connect
from estate_intelligence.utils.paths import repository_root

FINANCIAL_TABLES = (
    "evidence_financial_runs",
    "evidence_financial_case_catalogue",
    "evidence_financial_assumptions",
    "evidence_financial_recurring_costs",
    "evidence_financial_transition_costs",
    "evidence_financial_mitigation_costs",
    "evidence_financial_cashflows",
    "evidence_financial_payback",
    "evidence_financial_npv",
    "evidence_financial_cumulative_effects",
    "evidence_financial_sensitivity",
    "evidence_financial_break_even",
    "evidence_financial_risk_adjustments",
    "evidence_financial_confidence",
    "evidence_financial_comparison",
)

FORMULA_CATALOGUE_VERSION = "m10-formula-v1"


def run_financial_analysis(
    *,
    database_path: Path,
    config_path: Path = Path("config/finance.yaml"),
    output_dir: Path | None = None,
    rebuild: bool = False,
) -> dict[str, Any]:
    config = FinanceConfig.from_yaml(config_path)
    connection = connect(database_path)
    try:
        run_ids = _source_run_ids(connection)
        building_costs = latest_building_costs(connection)
        cases = build_financial_cases(connection, config)
        config_checksum = _file_checksum(config_path)
        case_checksum = _stable_checksum([case.model_dump(mode="json") for case in cases])
        assumption_checksum = _stable_checksum(config.model_dump(mode="json"))
        formula_checksum = _stable_checksum(FORMULA_CATALOGUE_VERSION)
        financial_run_id = _financial_run_id(
            config.framework_version,
            *run_ids.values(),
            config_checksum,
            case_checksum,
            assumption_checksum,
            formula_checksum,
        )
        evidence = _build_evidence(
            connection=connection,
            financial_run_id=financial_run_id,
            config=config,
            cases=cases,
            building_costs=building_costs,
        )
        readiness = _run_readiness(evidence.comparison)
        with connection:
            _create_tables(connection)
            if rebuild:
                _clear_tables(connection)
            elif _run_exists(connection, financial_run_id):
                raise FileExistsError(
                    "Refusing to overwrite existing financial evidence without --rebuild"
                )
            _insert_rows(connection, "evidence_financial_case_catalogue", evidence.cases)
            _insert_rows(connection, "evidence_financial_assumptions", evidence.assumptions)
            _insert_rows(connection, "evidence_financial_recurring_costs", evidence.recurring_costs)
            _insert_rows(
                connection, "evidence_financial_transition_costs", evidence.transition_costs
            )
            _insert_rows(
                connection, "evidence_financial_mitigation_costs", evidence.mitigation_costs
            )
            _insert_rows(connection, "evidence_financial_cashflows", evidence.cashflows)
            _insert_rows(connection, "evidence_financial_payback", evidence.payback)
            _insert_rows(connection, "evidence_financial_npv", evidence.npv)
            _insert_rows(
                connection, "evidence_financial_cumulative_effects", evidence.cumulative_effects
            )
            _insert_rows(connection, "evidence_financial_sensitivity", evidence.sensitivity)
            _insert_rows(connection, "evidence_financial_break_even", evidence.break_even)
            _insert_rows(
                connection, "evidence_financial_risk_adjustments", evidence.risk_adjustments
            )
            _insert_rows(connection, "evidence_financial_confidence", evidence.confidence)
            _insert_rows(connection, "evidence_financial_comparison", evidence.comparison)
            connection.execute(
                """
                INSERT INTO evidence_financial_runs
                (financial_run_id, ingestion_run_id, quality_run_id, utilisation_run_id,
                 forecast_run_id, scenario_run_id, optimisation_run_id, simulation_run_id,
                 framework_version, config_checksum, financial_case_catalogue_checksum,
                 assumption_catalogue_checksum, formula_catalogue_checksum, currency,
                 price_basis, analysis_horizon_years, discount_rate, annual_cost_escalation,
                 readiness_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    financial_run_id,
                    run_ids["ingestion_run_id"],
                    run_ids["quality_run_id"],
                    run_ids["utilisation_run_id"],
                    run_ids["forecast_run_id"],
                    run_ids["scenario_run_id"],
                    run_ids["optimisation_run_id"],
                    run_ids["simulation_run_id"],
                    config.framework_version,
                    config_checksum,
                    case_checksum,
                    assumption_checksum,
                    formula_checksum,
                    config.currency,
                    config.price_basis,
                    config.analysis_horizon_years,
                    config.discount_rate,
                    config.annual_cost_escalation,
                    readiness,
                ),
            )
        exports: dict[str, str] = {}
        if output_dir is not None:
            exports = {
                name: str(path)
                for name, path in export_financial_evidence(
                    connection, output_dir, financial_run_id
                ).items()
            }
        return {
            "financial_run_id": financial_run_id,
            **run_ids,
            "case_count": len(cases),
            "readiness_status": readiness,
            "config_checksum": config_checksum,
            "financial_case_catalogue_checksum": case_checksum,
            "assumption_catalogue_checksum": assumption_checksum,
            "formula_catalogue_checksum": formula_checksum,
            "exports": exports,
        }
    finally:
        connection.close()


def verify_financial_analysis(database_path: Path) -> dict[str, Any]:
    connection = connect(database_path)
    try:
        run = connection.execute(
            "SELECT * FROM evidence_financial_runs ORDER BY financial_run_id LIMIT 1"
        ).fetchone()
        if run is None:
            raise ValueError("No financial run evidence found")
        case_count = _count(connection, "evidence_financial_case_catalogue")
        comparison_count = _count(connection, "evidence_financial_comparison")
        cashflow_count = _count(connection, "evidence_financial_cashflows")
        if case_count != 7 or comparison_count < 21 or cashflow_count < 105:
            raise ValueError("Financial evidence is incomplete")
        return {
            "financial_run_id": run["financial_run_id"],
            "readiness_status": run["readiness_status"],
            "case_count": case_count,
            "comparison_rows": comparison_count,
            "cashflow_rows": cashflow_count,
        }
    finally:
        connection.close()


def export_existing_financial_evidence(database_path: Path, output_dir: Path) -> dict[str, Path]:
    connection = connect(database_path)
    try:
        row = connection.execute(
            "SELECT financial_run_id FROM evidence_financial_runs ORDER BY financial_run_id LIMIT 1"
        ).fetchone()
        if row is None:
            raise ValueError("No financial run evidence found")
        return export_financial_evidence(connection, output_dir, row["financial_run_id"])
    finally:
        connection.close()


def _build_evidence(
    *,
    connection: sqlite3.Connection,
    financial_run_id: str,
    config: FinanceConfig,
    cases: list[FinancialCase],
    building_costs: dict[str, dict[str, float]],
) -> FinanceEvidence:
    case_rows: list[dict[str, object]] = [
        {
            "financial_run_id": financial_run_id,
            "financial_case_id": case.financial_case_id,
            "source_type": case.source_type,
            "source_case_id": case.source_case_id,
            "simulation_case_id": case.simulation_case_id,
            "label": case.label,
        }
        for case in cases
    ]
    assumptions = assumption_rows(financial_run_id, config)
    recurring_rows: list[dict[str, object]] = []
    transition_rows: list[dict[str, object]] = []
    mitigation_rows: list[dict[str, object]] = []
    cashflow_rows: list[dict[str, object]] = []
    payback_rows: list[dict[str, object]] = []
    npv_rows: list[dict[str, object]] = []
    cumulative_rows: list[dict[str, object]] = []
    sensitivity_output: list[dict[str, object]] = []
    break_even_rows: list[dict[str, object]] = []
    risk_rows: list[dict[str, object]] = []
    confidence_rows: list[dict[str, object]] = []
    comparison_rows: list[dict[str, object]] = []

    for case in cases:
        recurring = recurring_cost_rows(
            financial_run_id=financial_run_id,
            config=config,
            case=case,
            building_costs=building_costs,
        )
        recurring_rows.extend(recurring)
        baseline_recurring = sum(_as_float(row["baseline_amount"]) for row in recurring)
        case_recurring = sum(_as_float(row["case_amount"]) for row in recurring)
        released_recurring = baseline_recurring - case_recurring
        curated_exit_cost = sum(
            building_costs[item]["exit_cost"] for item in case.released_buildings
        )
        transitions = transition_cost_rows(
            financial_run_id=financial_run_id,
            config=config,
            case=case,
            released_recurring_cost=released_recurring,
            curated_exit_cost=curated_exit_cost,
        )
        transition_rows.extend(transitions)
        mitigation = _mitigation_rows(connection, financial_run_id, config, case)
        mitigation_rows.extend(mitigation)
        total_transition = total_amount(transitions)
        annual_mitigation = total_amount(mitigation, "annual_amount")
        simulation_status = _simulation_status(connection, case.simulation_case_id)
        cap = realisability_cap(config, simulation_status)
        confidence_score = _confidence_score(case, simulation_status)
        confidence = confidence_status(confidence_score, config, simulation_status)
        case_readiness = readiness_status(
            total_transition * -1, simulation_status, annual_mitigation > 0
        )
        risk_rows.extend(
            _risk_rows(
                financial_run_id,
                case.financial_case_id,
                cap,
                simulation_status,
                confidence_score,
            )
        )
        confidence_rows.append(
            {
                "financial_run_id": financial_run_id,
                "financial_case_id": case.financial_case_id,
                "confidence_score": round(confidence_score, 4),
                "confidence_status": confidence,
                "readiness_status": case_readiness,
                "operational_resilience_flag": simulation_status,
                "not_realisable_without_mitigation": 1 if simulation_status == "fail" else 0,
            }
        )
        assumption_sets: list[tuple[str, AssumptionSetConfig]] = [
            ("base", config.base_case),
            ("optimistic", config.optimistic_case),
            ("pessimistic", config.pessimistic_case),
        ]
        base_npv = 0.0
        for assumption_name, assumption in assumption_sets:
            cashflows = annual_cashflows(
                config=config,
                assumption_name=assumption_name,
                assumption=assumption,
                financial_run_id=financial_run_id,
                financial_case_id=case.financial_case_id,
                baseline_recurring_cost=baseline_recurring,
                case_recurring_cost=case_recurring,
                transition_cost=total_transition,
                mitigation_cost=annual_mitigation,
            )
            cashflow_rows.extend(cashflows)
            values = [_as_float(row["net_annual_financial_effect"]) for row in cashflows]
            discounted = [_as_float(row["discounted_cash_flow"]) for row in cashflows]
            npv = net_present_value(values, config.discount_rate)
            if assumption_name == "base":
                base_npv = npv
            simple_payback = payback_year(values, str(config.payback_policy["not_reached_label"]))
            discounted_payback = payback_year(
                discounted, str(config.payback_policy["not_reached_label"])
            )
            payback_status = (
                "payback_reached" if simple_payback.isdigit() else "payback_not_reached"
            )
            payback_rows.append(
                {
                    "financial_run_id": financial_run_id,
                    "financial_case_id": case.financial_case_id,
                    "assumption_set": assumption_name,
                    "simple_payback_year": simple_payback,
                    "discounted_payback_year": discounted_payback,
                    "payback_status": payback_status,
                    "within_horizon": 1 if simple_payback.isdigit() else 0,
                }
            )
            npv_rows.append(
                {
                    "financial_run_id": financial_run_id,
                    "financial_case_id": case.financial_case_id,
                    "assumption_set": assumption_name,
                    "npv": round(npv, 4),
                    "discounted_initial_transition_cost": round(
                        _as_float(cashflows[0]["transition_costs"])
                        * _as_float(cashflows[0]["discount_factor"]),
                        4,
                    ),
                    "discount_rate": config.discount_rate,
                    "convention": str(config.npv_policy["discount_convention"]),
                }
            )
            cumulative_rows.append(
                {
                    "financial_run_id": financial_run_id,
                    "financial_case_id": case.financial_case_id,
                    "assumption_set": assumption_name,
                    "one_year_effect": round(values[0], 4),
                    "three_year_cumulative_effect": round(sum(values[:3]), 4),
                    "five_year_cumulative_effect": round(sum(values[:5]), 4),
                    "discounted_three_year_effect": round(sum(discounted[:3]), 4),
                    "discounted_five_year_effect": round(sum(discounted[:5]), 4),
                }
            )
            comparison_rows.append(
                {
                    "financial_run_id": financial_run_id,
                    "financial_case_id": case.financial_case_id,
                    "assumption_set": assumption_name,
                    "baseline_recurring_cost": round(baseline_recurring, 4),
                    "case_recurring_cost": round(case_recurring, 4),
                    "gross_recurring_cost_difference": round(released_recurring, 4),
                    "recurring_mitigation_cost": round(annual_mitigation, 4),
                    "net_annual_financial_effect": round(values[0], 4),
                    "total_transition_cost": round(total_transition, 4),
                    "npv": round(npv, 4),
                    "risk_adjusted_npv": round(npv * cap, 4),
                    "five_year_cumulative_effect": round(sum(values[:5]), 4),
                    "simple_payback_year": simple_payback,
                    "readiness_status": case_readiness,
                    "confidence_status": confidence,
                    "comparison_statement": _comparison_statement(case, simulation_status),
                }
            )
        sensitivity_output.extend(
            sensitivity_rows(
                financial_run_id=financial_run_id,
                config=config,
                financial_case_id=case.financial_case_id,
                baseline_recurring_cost=baseline_recurring,
                case_recurring_cost=case_recurring,
                transition_cost=total_transition,
                mitigation_cost=annual_mitigation,
                readiness_status=case_readiness,
                base_npv=base_npv,
            )
        )
        break_even_rows.extend(
            _break_even_rows(
                financial_run_id,
                case.financial_case_id,
                baseline_recurring - case_recurring,
                total_transition,
                annual_mitigation,
                config,
            )
        )
    return FinanceEvidence(
        cases=case_rows,
        assumptions=assumptions,
        recurring_costs=recurring_rows,
        transition_costs=transition_rows,
        mitigation_costs=mitigation_rows,
        cashflows=cashflow_rows,
        payback=payback_rows,
        npv=npv_rows,
        cumulative_effects=cumulative_rows,
        sensitivity=sensitivity_output,
        break_even=break_even_rows,
        risk_adjustments=risk_rows,
        confidence=confidence_rows,
        comparison=comparison_rows,
    )


def _mitigation_rows(
    connection: sqlite3.Connection,
    financial_run_id: str,
    config: FinanceConfig,
    case: FinancialCase,
) -> list[dict[str, object]]:
    failures = {
        str(row["failure_type"])
        for row in connection.execute(
            """
            SELECT DISTINCT failure_type FROM evidence_simulation_failures
            WHERE simulation_case_id = ?
            """,
            (case.simulation_case_id,),
        )
    }
    normal = connection.execute(
        """
        SELECT unserved_contacts, overtime_minutes
        FROM evidence_simulation_summary
        WHERE simulation_case_id = ? AND experiment_id = 'normal_operations'
        """,
        (case.simulation_case_id,),
    ).fetchone()
    workforce = connection.execute(
        """
        SELECT SUM(workforce_bottleneck_count) AS bottlenecks
        FROM evidence_simulation_workforce_metrics
        WHERE simulation_case_id = ? AND experiment_id = 'normal_operations'
        """,
        (case.simulation_case_id,),
    ).fetchone()
    rows = []
    for component, settings in sorted(config.operational_mitigation_costs.items()):
        linked = sorted(set(settings.applies_to_failure_types).intersection(failures))
        if not linked:
            continue
        amount = 0.0
        if settings.annual_cost_per_blocked_contact is not None:
            amount += float(normal["unserved_contacts"]) * settings.annual_cost_per_blocked_contact
        if settings.annual_cost_per_overtime_hour is not None:
            amount += (
                float(normal["overtime_minutes"]) / 60.0
            ) * settings.annual_cost_per_overtime_hour
        if settings.annual_cost_per_workforce_bottleneck is not None:
            amount += (
                float(workforce["bottlenecks"] or 0.0)
                * settings.annual_cost_per_workforce_bottleneck
            )
        if settings.annual_case_cost is not None:
            amount += settings.annual_case_cost
        rows.append(
            {
                "financial_run_id": financial_run_id,
                "financial_case_id": case.financial_case_id,
                "cost_component": component,
                "annual_amount": round(amount, 4),
                "trigger": ",".join(linked),
                "linked_failure_count": len(linked),
                "evidence_source": "evidence_simulation_failures",
                "inclusion_reason": "simulation threshold failure mitigation placeholder",
            }
        )
    return rows


def _risk_rows(
    financial_run_id: str,
    financial_case_id: str,
    cap: float,
    simulation_status: str,
    confidence_score: float,
) -> list[dict[str, object]]:
    return [
        {
            "financial_run_id": financial_run_id,
            "financial_case_id": financial_case_id,
            "factor_name": "simulation_resilience",
            "raw_factor_value": 1.0 if simulation_status == "pass" else 0.0,
            "adjusted_factor_value": cap,
            "effect_on_realisability": "caps risk-adjusted effect where simulation thresholds fail",
            "evidence_source": "evidence_simulation_summary",
        },
        {
            "financial_run_id": financial_run_id,
            "financial_case_id": financial_case_id,
            "factor_name": "financial_assumption_confidence",
            "raw_factor_value": round(confidence_score, 4),
            "adjusted_factor_value": round(confidence_score, 4),
            "effect_on_realisability": (
                "confidence status only; does not override operational failure"
            ),
            "evidence_source": "config/finance.yaml",
        },
    ]


def _break_even_rows(
    financial_run_id: str,
    financial_case_id: str,
    gross_difference: float,
    transition_cost: float,
    mitigation_cost: float,
    config: FinanceConfig,
) -> list[dict[str, object]]:
    annual_effects = [
        gross_difference - mitigation_cost for _ in range(config.analysis_horizon_years)
    ]
    return [
        {
            "financial_run_id": financial_run_id,
            "financial_case_id": financial_case_id,
            "break_even_metric": "maximum_transition_cost_before_zero_npv",
            "break_even_value": round(
                maximum_transition_cost_for_zero_npv(annual_effects, config.discount_rate), 4
            ),
            "interpretation": (
                "maximum transition cost before base undiscounted annual effects produce zero NPV"
            ),
        },
        {
            "financial_run_id": financial_run_id,
            "financial_case_id": financial_case_id,
            "break_even_metric": "minimum_annual_effect_for_five_year_payback",
            "break_even_value": round(minimum_annual_effect_for_payback(transition_cost, 5), 4),
            "interpretation": "annual effect required for simple payback by year five",
        },
        {
            "financial_run_id": financial_run_id,
            "financial_case_id": financial_case_id,
            "break_even_metric": "maximum_mitigation_cost_before_negative_annual_effect",
            "break_even_value": round(maximum_mitigation_before_negative(gross_difference), 4),
            "interpretation": "maximum recurring mitigation before annual effect becomes negative",
        },
    ]


def _comparison_statement(case: FinancialCase, simulation_status: str) -> str:
    if simulation_status == "fail":
        return (
            f"{case.label} retains nominal financial calculations, but is not financially "
            "realisable without operational mitigation because linked simulation thresholds failed."
        )
    return (
        f"{case.label} is analytical financial evidence only, not an implementation recommendation."
    )


def _confidence_score(case: FinancialCase, simulation_status: str) -> float:
    score = 0.82
    if case.source_type == "scenario":
        score -= 0.05
    if not case.release_supported and case.source_type != "baseline":
        score -= 0.08
    if simulation_status == "fail":
        score -= 0.25
    return max(0.0, score)


def _simulation_status(connection: sqlite3.Connection, simulation_case_id: str) -> str:
    row = connection.execute(
        """
        SELECT SUM(CASE WHEN status = 'fail' THEN 1 ELSE 0 END) AS failures
        FROM evidence_simulation_summary
        WHERE simulation_case_id = ?
        """,
        (simulation_case_id,),
    ).fetchone()
    return "fail" if int(row["failures"] or 0) > 0 else "pass"


def _run_readiness(comparison_rows: list[dict[str, object]]) -> str:
    statuses = {str(row["readiness_status"]) for row in comparison_rows}
    if "not_realisable_without_mitigation" in statuses:
        return "review_required"
    if "financially_negative" in statuses:
        return "review_required"
    return "financially_positive"


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
        "simulation_run_id": (
            "SELECT simulation_run_id AS id "
            "FROM evidence_simulation_runs ORDER BY simulation_run_id LIMIT 1"
        ),
    }
    result: dict[str, str] = {}
    for key, query in queries.items():
        row = connection.execute(query).fetchone()
        if row is None:
            raise ValueError("Completed upstream ingestion through simulation evidence is required")
        result[key] = str(row["id"])
    return result


def _create_tables(connection: sqlite3.Connection) -> None:
    schema = repository_root() / "database" / "schema" / "012_financial_tables.sql"
    connection.executescript(schema.read_text(encoding="utf-8"))


def _clear_tables(connection: sqlite3.Connection) -> None:
    for table in reversed(FINANCIAL_TABLES):
        connection.execute(f"DELETE FROM {table}")


def _insert_rows(
    connection: sqlite3.Connection, table_name: str, rows: list[dict[str, object]]
) -> None:
    if not rows:
        return
    columns = list(rows[0])
    placeholders = ", ".join(["?"] * len(columns))
    quoted = ", ".join(columns)
    values = [tuple(row[column] for column in columns) for row in rows]
    connection.executemany(
        f"INSERT INTO {table_name} ({quoted}) VALUES ({placeholders})",
        values,
    )


def _run_exists(connection: sqlite3.Connection, financial_run_id: str) -> bool:
    try:
        row = connection.execute(
            "SELECT financial_run_id FROM evidence_financial_runs WHERE financial_run_id = ?",
            (financial_run_id,),
        ).fetchone()
    except sqlite3.OperationalError:
        return False
    return row is not None


def _count(connection: sqlite3.Connection, table: str) -> int:
    return int(connection.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()["count"])


def _financial_run_id(*parts: str) -> str:
    return f"FIN-{hashlib.sha256(json.dumps(parts, sort_keys=True).encode()).hexdigest()[:16]}"


def _file_checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _stable_checksum(payload: object) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def _as_float(value: object) -> float:
    if isinstance(value, int | float | str):
        return float(value)
    raise TypeError(f"Expected numeric financial value, got {type(value)}")
