# ruff: noqa: E501
"""Shared read-only dashboard services over persisted milestone evidence."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dashboard.data.queries import REQUIRED_EVIDENCE_TABLES
from dashboard.data.repository import DEFAULT_DATABASE, DashboardRepository


@dataclass(frozen=True)
class DashboardSummary:
    """Structured validation result for CLI checks and pages."""

    ok: bool
    database: str
    missing_tables: tuple[str, ...]
    run_lineage: dict[str, str]
    warnings: tuple[str, ...]


class DashboardService:
    """Application service consumed by Streamlit pages and CLI checks."""

    def __init__(self, database_path: Path = DEFAULT_DATABASE) -> None:
        self.repository = DashboardRepository(database_path)

    def validate(self) -> DashboardSummary:
        missing = tuple(self.repository.validate_required_tables(REQUIRED_EVIDENCE_TABLES))
        lineage = {} if missing else self.get_run_lineage()
        warnings = tuple(self._global_warnings())
        return DashboardSummary(
            ok=not missing and len(lineage) == 8,
            database=str(self.repository.database_path),
            missing_tables=missing,
            run_lineage=lineage,
            warnings=warnings,
        )

    def assert_read_only(self) -> bool:
        return self.repository.assert_write_blocked()

    def get_run_lineage(self) -> dict[str, str]:
        return self.repository.get_run_lineage()

    def get_executive_summary(self) -> dict[str, Any]:
        lineage = self.get_run_lineage()
        utilisation_run = lineage.get("utilisation", "")
        quality_run = lineage.get("quality", "")
        forecast_run = lineage.get("forecast", "")
        scenario_run = lineage.get("scenario", "")
        optimisation_run = lineage.get("optimisation", "")
        simulation_run = lineage.get("simulation", "")
        financial_run = lineage.get("financial", "")
        counts = (
            self.repository.fetch_one(
                """
            SELECT
              (SELECT COUNT(*) FROM curated_sites) AS site_count,
              (SELECT COUNT(*) FROM curated_buildings WHERE active_flag = 'true') AS building_count,
              (SELECT COUNT(*) FROM evidence_room_utilisation WHERE utilisation_run_id = ?) AS room_count,
              (SELECT COUNT(*) FROM evidence_scenario_comparison WHERE scenario_run_id = ?) AS scenario_count,
              (SELECT COUNT(*) FROM evidence_optimisation_cases WHERE optimisation_run_id = ?) AS optimisation_case_count,
              (SELECT COUNT(*) FROM evidence_quality_manual_review_queue WHERE quality_run_id = ? AND status = 'open') AS manual_review_count
            """,
                (utilisation_run, scenario_run, optimisation_run, quality_run),
            )
            or {}
        )
        quality = (
            self.repository.fetch_one(
                "SELECT overall_score, overall_status FROM evidence_quality_runs WHERE quality_run_id = ?",
                (quality_run,),
            )
            or {}
        )
        utilisation = (
            self.repository.fetch_one(
                """
            SELECT overall_booked_utilisation, overall_actual_utilisation,
                   overall_effective_utilisation, readiness_status
            FROM evidence_utilisation_runs WHERE utilisation_run_id = ?
            """,
                (utilisation_run,),
            )
            or {}
        )
        forecast = (
            self.repository.fetch_one(
                """
            SELECT historical_start_period, historical_end_period, forecast_horizon, readiness_status
            FROM evidence_forecast_runs WHERE forecast_run_id = ?
            """,
                (forecast_run,),
            )
            or {}
        )
        simulation = (
            self.repository.fetch_one(
                "SELECT readiness_status FROM evidence_simulation_runs WHERE simulation_run_id = ?",
                (simulation_run,),
            )
            or {}
        )
        financial = (
            self.repository.fetch_one(
                """
            SELECT readiness_status, analysis_horizon_years
            FROM evidence_financial_runs WHERE financial_run_id = ?
            """,
                (financial_run,),
            )
            or {}
        )
        financial_base = (
            self.repository.fetch_one(
                """
            SELECT baseline_recurring_cost, MAX(npv) AS highest_nominal_npv,
                   MAX(risk_adjusted_npv) AS highest_risk_adjusted_npv
            FROM evidence_financial_comparison
            WHERE financial_run_id = ? AND assumption_set = 'base'
            """,
                (financial_run,),
            )
            or {}
        )
        return {
            "lineage": lineage,
            **counts,
            **quality,
            **utilisation,
            **forecast,
            "simulation_readiness": simulation.get("readiness_status", "insufficient_evidence"),
            "financial_readiness": financial.get("readiness_status", "insufficient_evidence"),
            **financial_base,
            "warnings": self._global_warnings(),
        }

    def get_estate_portfolio(self, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        filters = filters or {}
        where = ["1 = 1"]
        params: list[Any] = []
        for key, column in (
            ("site_id", "b.site_id"),
            ("ownership_type", "b.ownership_type"),
            ("building_type", "b.building_type"),
            ("active_flag", "b.active_flag"),
        ):
            if filters.get(key):
                where.append(f"{column} = ?")
                params.append(filters[key])
        utilisation_run = self.get_run_lineage().get("utilisation", "")
        params.insert(0, utilisation_run)
        return self.repository.fetch_all(
            f"""
            SELECT b.site_id, b.building_id, b.building_name, b.ownership_type, b.building_type,
                   CAST(b.floor_area_m2 AS REAL) AS floor_area_m2, b.condition_rating,
                   b.accessibility_rating, b.active_flag, b.lease_start_date, b.lease_end_date,
                   COALESCE(u.actual_utilisation, 0) AS actual_utilisation,
                   COALESCE(u.effective_utilisation, 0) AS effective_utilisation,
                   COALESCE(uc.annual_operating_cost, 0) AS annual_operating_cost,
                   COALESCE(uc.cost_per_completed_contact, 0) AS cost_per_completed_contact,
                   COUNT(r.room_id) AS room_count,
                   SUM(CASE WHEN r.protected_capacity_flag = 'true' THEN 1 ELSE 0 END) AS protected_room_count
            FROM curated_buildings b
            LEFT JOIN curated_rooms r ON r.building_id = b.building_id
            LEFT JOIN evidence_building_utilisation u
              ON u.building_id = b.building_id AND u.utilisation_run_id = ?
            LEFT JOIN evidence_unit_cost_metrics uc
              ON uc.building_id = b.building_id AND uc.utilisation_run_id = ?
            WHERE {" AND ".join(where)}
            GROUP BY b.building_id
            ORDER BY b.site_id, b.building_id
            """,
            tuple([utilisation_run, *params]),
        )

    def get_room_utilisation(self, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        filters = filters or {}
        where = ["ru.utilisation_run_id = ?"]
        params: list[Any] = [self.get_run_lineage().get("utilisation", "")]
        mapping = {
            "site_id": "ru.site_id",
            "building_id": "ru.building_id",
            "room_type": "r.room_type",
            "protected_capacity_flag": "ru.protected_capacity_flag",
            "persistent_flag": "uf.persistent_flag",
        }
        for key, column in mapping.items():
            if filters.get(key) not in (None, ""):
                where.append(f"{column} = ?")
                params.append(filters[key])
        return self.repository.fetch_all(
            f"""
            SELECT ru.*, r.room_name, r.room_type, r.capacity, r.specialist_equipment,
                   r.accessible_flag, COALESCE(uf.persistent_flag, 0) AS persistent_flag,
                   uf.releasable_classification, uf.months_below_threshold
            FROM evidence_room_utilisation ru
            LEFT JOIN curated_rooms r ON r.room_id = ru.room_id
            LEFT JOIN evidence_underutilisation_flags uf
              ON uf.room_id = ru.room_id AND uf.utilisation_run_id = ru.utilisation_run_id
            WHERE {" AND ".join(where)}
            ORDER BY ru.effective_utilisation, ru.room_id
            LIMIT 250
            """,
            tuple(params),
        )

    def get_clinical_activity(self, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        filters = filters or {}
        where = ["1 = 1"]
        params: list[Any] = []
        if filters.get("service_id"):
            where.append("a.service_id = ?")
            params.append(filters["service_id"])
        if filters.get("site_id"):
            where.append("v.site_id = ?")
            params.append(filters["site_id"])
        return self.repository.fetch_all(
            f"""
            SELECT substr(a.activity_date, 1, 7) AS period, a.service_id, s.service_name,
                   v.site_id, a.appointment_type,
                   SUM(CAST(a.scheduled_contacts AS INTEGER)) AS scheduled_contacts,
                   SUM(CAST(a.completed_contacts AS INTEGER)) AS completed_contacts,
                   SUM(CAST(a.face_to_face_contacts AS INTEGER)) AS face_to_face_contacts,
                   SUM(CAST(a.remote_contacts AS INTEGER)) AS remote_contacts,
                   SUM(CAST(a.did_not_attend_count AS INTEGER)) AS dna_contacts,
                   SUM(CAST(a.cancelled_contacts AS INTEGER)) AS cancellations,
                   AVG(CAST(a.average_contact_duration_minutes AS REAL)) AS average_duration_minutes
            FROM curated_clinical_activity a
            LEFT JOIN curated_activity_context_view v ON v.activity_id = a.activity_id
            LEFT JOIN curated_services s ON s.service_id = a.service_id
            WHERE {" AND ".join(where)}
            GROUP BY period, a.service_id, v.site_id, a.appointment_type
            ORDER BY period, a.service_id
            LIMIT 250
            """,
            tuple(params),
        )

    def get_workforce_metrics(self, filters: dict[str, Any] | None = None) -> dict[str, Any]:
        filters = filters or {}
        where = ["1 = 1"]
        params: list[Any] = []
        for key, column in (
            ("service_id", "w.service_id"),
            ("site_id", "w.site_id"),
            ("staff_group", "w.staff_group"),
        ):
            if filters.get(key):
                where.append(f"{column} = ?")
                params.append(filters[key])
        rows = self.repository.fetch_all(
            f"""
            SELECT substr(w.record_date, 1, 7) AS period, w.service_id, s.service_name, w.site_id,
                   w.staff_group, SUM(CAST(w.planned_fte AS REAL)) AS planned_fte,
                   SUM(CAST(w.available_fte AS REAL)) AS available_fte,
                   AVG(CAST(w.absence_rate AS REAL)) AS absence_rate,
                   AVG(CAST(w.vacancy_rate AS REAL)) AS vacancy_rate,
                   AVG(CAST(w.remote_working_rate AS REAL)) AS remote_working_rate,
                   SUM(CAST(w.session_capacity AS REAL)) AS session_capacity
            FROM curated_workforce w
            LEFT JOIN curated_services s ON s.service_id = w.service_id
            WHERE {" AND ".join(where)}
            GROUP BY period, w.service_id, w.site_id, w.staff_group
            ORDER BY period, w.service_id
            LIMIT 250
            """,
            tuple(params),
        )
        sim_run = self.get_run_lineage().get("simulation", "")
        bottlenecks = self.repository.fetch_all(
            """
            SELECT simulation_case_id, experiment_id, service_id,
                   AVG(workforce_utilisation) AS workforce_utilisation,
                   SUM(blocked_demand_contacts) AS blocked_demand_contacts,
                   SUM(workforce_bottleneck_count) AS bottleneck_count
            FROM evidence_simulation_workforce_metrics
            WHERE simulation_run_id = ?
            GROUP BY simulation_case_id, experiment_id, service_id
            ORDER BY bottleneck_count DESC, blocked_demand_contacts DESC
            LIMIT 100
            """,
            (sim_run,),
        )
        return {"workforce": rows, "simulation_bottlenecks": bottlenecks}

    def get_data_quality_summary(self) -> dict[str, Any]:
        quality_run = self.get_run_lineage().get("quality", "")
        return {
            "run": self.repository.fetch_one(
                "SELECT * FROM evidence_quality_runs WHERE quality_run_id = ?", (quality_run,)
            ),
            "dataset_scores": self.repository.fetch_all(
                "SELECT * FROM evidence_quality_dataset_scores WHERE quality_run_id = ? ORDER BY dataset",
                (quality_run,),
            ),
            "dimension_scores": self.repository.fetch_all(
                "SELECT * FROM evidence_quality_dimension_scores WHERE quality_run_id = ? ORDER BY dataset, dimension",
                (quality_run,),
            ),
            "issues": self.repository.fetch_all(
                "SELECT severity, failure_action, status, COUNT(*) AS issue_count FROM evidence_quality_record_issues WHERE quality_run_id = ? GROUP BY severity, failure_action, status ORDER BY severity",
                (quality_run,),
            ),
            "manual_review": self.repository.fetch_all(
                "SELECT * FROM evidence_quality_manual_review_queue WHERE quality_run_id = ? ORDER BY severity, dataset",
                (quality_run,),
            ),
            "intentional_detection": self.repository.fetch_all(
                "SELECT * FROM evidence_intentional_issue_detection ORDER BY issue_id"
            ),
            "reconciliation": self.repository.fetch_all(
                "SELECT * FROM evidence_reconciliation_summary ORDER BY dataset"
            ),
            "exclusions": self.repository.fetch_all(
                "SELECT dataset, analytical_effect, COUNT(*) AS row_count FROM evidence_analytics_exclusions GROUP BY dataset, analytical_effect ORDER BY dataset"
            ),
        }

    def get_forecast_summary(self, filters: dict[str, Any] | None = None) -> dict[str, Any]:
        filters = filters or {}
        forecast_run = self.get_run_lineage().get("forecast", "")
        where = ["e.forecast_run_id = ?"]
        params: list[Any] = [forecast_run]
        for key, column in (
            ("target", "e.target"),
            ("entity_type", "e.entity_type"),
            ("eligibility_status", "e.eligibility_status"),
        ):
            if filters.get(key):
                where.append(f"{column} = ?")
                params.append(filters[key])
        return {
            "run": self.repository.fetch_one(
                "SELECT * FROM evidence_forecast_runs WHERE forecast_run_id = ?", (forecast_run,)
            ),
            "eligibility": self.repository.fetch_all(
                f"SELECT e.* FROM evidence_forecast_eligibility e WHERE {' AND '.join(where)} ORDER BY e.target, e.entity_id LIMIT 200",
                tuple(params),
            ),
            "selections": self.repository.fetch_all(
                "SELECT * FROM evidence_forecast_selections WHERE forecast_run_id = ? ORDER BY series_id LIMIT 200",
                (forecast_run,),
            ),
            "accuracy": self.repository.fetch_all(
                "SELECT * FROM evidence_forecast_model_results WHERE forecast_run_id = ? ORDER BY series_id, model_id LIMIT 200",
                (forecast_run,),
            ),
            "values": self.repository.fetch_all(
                "SELECT * FROM evidence_forecast_values WHERE forecast_run_id = ? ORDER BY series_id, period LIMIT 250",
                (forecast_run,),
            ),
            "intervals": self.repository.fetch_all(
                "SELECT * FROM evidence_forecast_intervals WHERE forecast_run_id = ? ORDER BY series_id, period, interval_level LIMIT 250",
                (forecast_run,),
            ),
        }

    def get_scenario_comparison(self) -> dict[str, Any]:
        scenario_run = self.get_run_lineage().get("scenario", "")
        return {
            "comparison": self.repository.fetch_all(
                "SELECT * FROM evidence_scenario_comparison WHERE scenario_run_id = ? ORDER BY scenario_id",
                (scenario_run,),
            ),
            "costs": self.repository.fetch_all(
                "SELECT * FROM evidence_scenario_costs WHERE scenario_run_id = ? ORDER BY scenario_id",
                (scenario_run,),
            ),
            "workforce": self.repository.fetch_all(
                "SELECT * FROM evidence_scenario_workforce WHERE scenario_run_id = ? ORDER BY scenario_id, service_id LIMIT 200",
                (scenario_run,),
            ),
            "accessibility": self.repository.fetch_all(
                "SELECT * FROM evidence_scenario_accessibility WHERE scenario_run_id = ? ORDER BY scenario_id, site_id",
                (scenario_run,),
            ),
            "risks": self.repository.fetch_all(
                "SELECT * FROM evidence_scenario_risks WHERE scenario_run_id = ? ORDER BY scenario_id, risk_category",
                (scenario_run,),
            ),
            "room_actions": self.repository.fetch_all(
                "SELECT * FROM evidence_scenario_room_actions WHERE scenario_run_id = ? ORDER BY scenario_id, room_id LIMIT 250",
                (scenario_run,),
            ),
        }

    def get_optimisation_summary(self) -> dict[str, Any]:
        optimisation_run = self.get_run_lineage().get("optimisation", "")
        return {
            "run": self.repository.fetch_one(
                "SELECT * FROM evidence_optimisation_runs WHERE optimisation_run_id = ?",
                (optimisation_run,),
            ),
            "cases": self.repository.fetch_all(
                "SELECT * FROM evidence_optimisation_cases WHERE optimisation_run_id = ? ORDER BY case_id",
                (optimisation_run,),
            ),
            "comparison": self.repository.fetch_all(
                "SELECT * FROM evidence_optimisation_comparison WHERE optimisation_run_id = ? ORDER BY case_id",
                (optimisation_run,),
            ),
            "objective": self.repository.fetch_all(
                "SELECT * FROM evidence_optimisation_objective_components WHERE optimisation_run_id = ? ORDER BY case_id, component",
                (optimisation_run,),
            ),
            "constraints": self.repository.fetch_all(
                "SELECT * FROM evidence_optimisation_binding_constraints WHERE optimisation_run_id = ? ORDER BY case_id, constraint_family, constraint_id LIMIT 200",
                (optimisation_run,),
            ),
            "building_status": self.repository.fetch_all(
                "SELECT * FROM evidence_optimisation_building_status WHERE optimisation_run_id = ? ORDER BY case_id, building_id",
                (optimisation_run,),
            ),
            "allocations": self.repository.fetch_all(
                "SELECT * FROM evidence_optimisation_allocations WHERE optimisation_run_id = ? ORDER BY case_id, service_id, room_id LIMIT 250",
                (optimisation_run,),
            ),
        }

    def get_simulation_summary(self) -> dict[str, Any]:
        simulation_run = self.get_run_lineage().get("simulation", "")
        return {
            "run": self.repository.fetch_one(
                "SELECT * FROM evidence_simulation_runs WHERE simulation_run_id = ?",
                (simulation_run,),
            ),
            "cases": self.repository.fetch_all(
                "SELECT * FROM evidence_simulation_cases WHERE simulation_run_id = ? ORDER BY simulation_case_id",
                (simulation_run,),
            ),
            "experiments": self.repository.fetch_all(
                "SELECT * FROM evidence_simulation_experiments WHERE simulation_run_id = ? ORDER BY experiment_id",
                (simulation_run,),
            ),
            "resilience": self.repository.fetch_all(
                "SELECT * FROM evidence_simulation_resilience_metrics WHERE simulation_run_id = ? ORDER BY simulation_case_id, experiment_id",
                (simulation_run,),
            ),
            "summary": self.repository.fetch_all(
                "SELECT * FROM evidence_simulation_summary WHERE simulation_run_id = ? ORDER BY simulation_case_id, experiment_id",
                (simulation_run,),
            ),
            "thresholds": self.repository.fetch_all(
                "SELECT * FROM evidence_simulation_threshold_results WHERE simulation_run_id = ? ORDER BY result_status, threshold_name",
                (simulation_run,),
            ),
            "workforce": self.repository.fetch_all(
                "SELECT * FROM evidence_simulation_workforce_metrics WHERE simulation_run_id = ? ORDER BY workforce_bottleneck_count DESC LIMIT 250",
                (simulation_run,),
            ),
        }

    def get_financial_summary(self) -> dict[str, Any]:
        financial_run = self.get_run_lineage().get("financial", "")
        return {
            "run": self.repository.fetch_one(
                "SELECT * FROM evidence_financial_runs WHERE financial_run_id = ?", (financial_run,)
            ),
            "cases": self.repository.fetch_all(
                "SELECT * FROM evidence_financial_case_catalogue WHERE financial_run_id = ? ORDER BY financial_case_id",
                (financial_run,),
            ),
            "comparison": self.repository.fetch_all(
                "SELECT * FROM evidence_financial_comparison WHERE financial_run_id = ? ORDER BY assumption_set, financial_case_id",
                (financial_run,),
            ),
            "cashflows": self.repository.fetch_all(
                "SELECT * FROM evidence_financial_cashflows WHERE financial_run_id = ? ORDER BY financial_case_id, assumption_set, analysis_year",
                (financial_run,),
            ),
            "cumulative": self.repository.fetch_all(
                "SELECT * FROM evidence_financial_cumulative_effects WHERE financial_run_id = ? ORDER BY financial_case_id, assumption_set",
                (financial_run,),
            ),
            "sensitivity": self.repository.fetch_all(
                "SELECT * FROM evidence_financial_sensitivity WHERE financial_run_id = ? ORDER BY ABS(tornado_impact) DESC, financial_case_id LIMIT 250",
                (financial_run,),
            ),
            "break_even": self.repository.fetch_all(
                "SELECT * FROM evidence_financial_break_even WHERE financial_run_id = ? ORDER BY financial_case_id, break_even_metric",
                (financial_run,),
            ),
            "confidence": self.repository.fetch_all(
                "SELECT * FROM evidence_financial_confidence WHERE financial_run_id = ? ORDER BY financial_case_id",
                (financial_run,),
            ),
            "transition_costs": self.repository.fetch_all(
                "SELECT * FROM evidence_financial_transition_costs WHERE financial_run_id = ? ORDER BY financial_case_id, amount DESC",
                (financial_run,),
            ),
        }

    def get_limitations(self) -> dict[str, Any]:
        lineage = self.get_run_lineage()
        tables = self.repository.fetch_all(
            """
            SELECT name AS table_name
            FROM sqlite_master sm
            WHERE type = 'table' AND name LIKE 'evidence_%'
            ORDER BY name
            """
        )
        row_counts = [
            {
                "table_name": row["table_name"],
                "row_count": (
                    self.repository.fetch_one(
                        f"SELECT COUNT(*) AS row_count FROM {row['table_name']}"
                    )
                    or {"row_count": 0}
                )["row_count"],
            }
            for row in tables
        ]
        return {
            "lineage": lineage,
            "row_counts": row_counts,
            "boundaries": [
                "Synthetic demonstration only.",
                "No real patient or estate data.",
                "No final recommendation or approval workflow.",
                "No external APIs, public deployment, authentication, or Power BI artefacts.",
            ],
        }

    def get_communication_summary(self) -> dict[str, Any]:
        if not self.repository.table_exists("evidence_communication_runs"):
            return {
                "runs": [],
                "options": [],
                "objections": [],
                "challenges": [],
                "revisions": [],
                "claims": [],
                "decision_records": [],
            }
        run = self.repository.fetch_one(
            "SELECT * FROM evidence_communication_runs ORDER BY communication_run_id DESC LIMIT 1"
        )
        communication_run_id = str(run["communication_run_id"]) if run else ""
        return {
            "runs": [run] if run else [],
            "options": self.repository.fetch_all(
                "SELECT * FROM evidence_communication_options WHERE communication_run_id = ? ORDER BY option_id",
                (communication_run_id,),
            ),
            "objections": self.repository.fetch_all(
                "SELECT * FROM evidence_communication_objections WHERE communication_run_id = ? ORDER BY objection_id",
                (communication_run_id,),
            ),
            "challenges": self.repository.fetch_all(
                "SELECT * FROM evidence_communication_challenges WHERE communication_run_id = ? ORDER BY challenge_id",
                (communication_run_id,),
            ),
            "revisions": self.repository.fetch_all(
                "SELECT * FROM evidence_communication_revisions WHERE communication_run_id = ? ORDER BY revision_id",
                (communication_run_id,),
            ),
            "claims": self.repository.fetch_all(
                "SELECT * FROM evidence_communication_claims WHERE communication_run_id = ? ORDER BY claim_id",
                (communication_run_id,),
            ),
            "decision_records": self.repository.fetch_all(
                "SELECT * FROM evidence_communication_decision_records WHERE communication_run_id = ? ORDER BY decision_record_id",
                (communication_run_id,),
            ),
        }

    def _global_warnings(self) -> list[str]:
        warnings: list[str] = [
            "Synthetic demonstration only.",
            "No real patient or estate data.",
            "No estate decision is approved by this application.",
        ]
        lineage = (
            self.repository.get_run_lineage() if self.repository.database_path.exists() else {}
        )
        simulation_run = lineage.get("simulation")
        financial_run = lineage.get("financial")
        if simulation_run:
            row = self.repository.fetch_one(
                "SELECT readiness_status FROM evidence_simulation_runs WHERE simulation_run_id = ?",
                (simulation_run,),
            )
            if row and row.get("readiness_status") == "review_required":
                warnings.append("Simulation readiness is review_required.")
        if financial_run:
            rows = self.repository.fetch_all(
                """
                SELECT COUNT(*) AS failing_cases
                FROM evidence_financial_confidence
                WHERE financial_run_id = ?
                  AND readiness_status = 'not_realisable_without_mitigation'
                """,
                (financial_run,),
            )
            if rows and rows[0].get("failing_cases", 0):
                warnings.append("Financial confidence is not_realisable_without_mitigation.")
        return warnings
