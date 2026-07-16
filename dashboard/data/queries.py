"""Named SQL queries used by the read-only dashboard repository."""

from __future__ import annotations

RUN_TABLES: dict[str, tuple[str, str]] = {
    "ingestion": ("evidence_ingestion_runs", "ingestion_run_id"),
    "quality": ("evidence_quality_runs", "quality_run_id"),
    "utilisation": ("evidence_utilisation_runs", "utilisation_run_id"),
    "forecast": ("evidence_forecast_runs", "forecast_run_id"),
    "scenario": ("evidence_scenario_runs", "scenario_run_id"),
    "optimisation": ("evidence_optimisation_runs", "optimisation_run_id"),
    "simulation": ("evidence_simulation_runs", "simulation_run_id"),
    "financial": ("evidence_financial_runs", "financial_run_id"),
}

REQUIRED_EVIDENCE_TABLES: tuple[str, ...] = (
    "curated_sites",
    "curated_buildings",
    "curated_rooms",
    "curated_services",
    "curated_clinical_activity",
    "curated_workforce",
    "curated_finance",
    "evidence_ingestion_runs",
    "evidence_quality_runs",
    "evidence_utilisation_runs",
    "evidence_forecast_runs",
    "evidence_scenario_runs",
    "evidence_optimisation_runs",
    "evidence_simulation_runs",
    "evidence_financial_runs",
    "evidence_room_utilisation",
    "evidence_building_utilisation",
    "evidence_financial_comparison",
)

READ_ONLY_TABLE_PREFIXES: tuple[str, ...] = ("curated_", "evidence_")
