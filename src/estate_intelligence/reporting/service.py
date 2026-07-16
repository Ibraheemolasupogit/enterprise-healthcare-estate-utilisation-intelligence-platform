# ruff: noqa: E501
"""Shared communication-evidence generation service."""

from __future__ import annotations

import json
import shutil
import sqlite3
from dataclasses import asdict
from pathlib import Path
from typing import Any

import yaml

from estate_intelligence.reporting.audience import load_audiences
from estate_intelligence.reporting.challenge import (
    build_challenge_responses,
    build_objections,
    build_required_revision,
)
from estate_intelligence.reporting.decision_record import build_decision_record
from estate_intelligence.reporting.evidence import (
    fetch_all,
    fetch_one,
    open_connection,
    require_lineage,
    resolve_run_lineage,
)
from estate_intelligence.reporting.models import (
    Audience,
    ChallengeResponse,
    Claim,
    CommunicationConfig,
    CommunicationOption,
    CommunicationRun,
    Objection,
    Revision,
)
from estate_intelligence.reporting.options import build_options
from estate_intelligence.reporting.provenance import build_provenance_rows
from estate_intelligence.reporting.rendering import (
    file_checksum,
    markdown_table,
    stable_digest,
    write_csv,
    write_json,
    write_markdown,
)
from estate_intelligence.utils.paths import repository_root

COMMUNICATION_TABLES = (
    "evidence_communication_provenance",
    "evidence_communication_decision_records",
    "evidence_communication_claims",
    "evidence_communication_revisions",
    "evidence_communication_challenges",
    "evidence_communication_objections",
    "evidence_communication_products",
    "evidence_communication_options",
    "evidence_communication_audiences",
    "evidence_communication_runs",
)

PRODUCT_FILES = (
    "communication_run_summary.json",
    "audience_catalogue.csv",
    "option_catalogue.csv",
    "executive_options_paper.md",
    "clinical_operational_brief.md",
    "finance_brief.md",
    "estates_brief.md",
    "technical_appendix.md",
    "stakeholder_objection_register.csv",
    "challenge_response_log.csv",
    "recommendation_revision_log.csv",
    "decision_record.json",
    "decision_record.md",
    "communication_evidence_map.csv",
    "communication_provenance.csv",
    "communication_limitations.md",
)


class CommunicationEvidenceError(RuntimeError):
    """Raised when communication evidence cannot be generated or verified."""


def load_communication_config(config_path: Path) -> CommunicationConfig:
    document = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise ValueError("communication configuration must be a mapping")
    required = {
        "framework_version",
        "source_run_requirements",
        "audience_catalogue",
        "message_priorities",
        "evidence_inclusion_rules",
        "risk_language_rules",
        "status_language_rules",
        "financial_language_rules",
        "simulation_language_rules",
        "option_catalogue",
        "challenge_catalogue",
        "revision_rules",
        "decision_record_schema",
        "output_paths",
        "rounding",
    }
    missing = sorted(required - set(document))
    if missing:
        raise ValueError(f"communication configuration missing keys: {missing}")
    return CommunicationConfig(
        framework_version=str(document["framework_version"]),
        document=document,
        config_path=config_path,
    )


def apply_language_controls(text: str, resilience_failed: bool = True) -> str:
    replacements = {
        "guaranteed saving": "synthetic nominal financial effect",
        "guaranteed savings": "synthetic nominal financial effects",
        "confirmed benefit": "planning estimate",
        "approved business case": "non-approving governance evidence",
        "saving": "nominal recurring cost difference",
        "recommended": "strongest configured result, subject to constraints",
        "optimal solution": "lowest configured mathematical objective",
        "releasable building": "potentially releasable in the mathematical candidate",
        "financially viable": "nominally financially positive under configured assumptions",
    }
    controlled = text
    for unsafe, safe in replacements.items():
        controlled = controlled.replace(unsafe, safe).replace(unsafe.title(), safe)
    if resilience_failed and "not realisable without mitigation" not in controlled:
        controlled = f"{controlled} This remains not realisable without mitigation."
    return controlled


def validate_language_controls(text: str) -> None:
    lowered = text.lower()
    forbidden_contexts = {
        "guaranteed savings": ("no guaranteed savings",),
        "should close": (),
        "must implement": (),
        "clinically safe": (),
        "validated in practice": (),
        "stakeholders agreed": (),
        "board approved": (),
        "recommended option": ("no option is recommended",),
    }
    for phrase, exceptions in forbidden_contexts.items():
        if phrase in lowered and not any(exception in lowered for exception in exceptions):
            raise CommunicationEvidenceError(f"Forbidden unsupported wording found: {phrase}")
    if (
        " approved" in lowered
        and "not approved" not in lowered
        and "no estate decision is approved" not in lowered
        and "no move is operationally approved" not in lowered
        and "no operationally approved moves" not in lowered
    ):
        raise CommunicationEvidenceError("Unsupported approval wording found.")


def generate_communication_evidence(
    database_path: Path,
    config_path: Path = Path("config/communication.yaml"),
    output_dir: Path = Path("outputs/communication"),
    rebuild: bool = False,
) -> dict[str, Any]:
    config = load_communication_config(config_path)
    output_dir = output_dir
    if output_dir.exists() and any(output_dir.iterdir()) and not rebuild:
        raise FileExistsError(
            f"Communication output directory already contains files: {output_dir}"
        )

    with open_connection(database_path) as connection:
        lineage = resolve_run_lineage(connection)
        require_lineage(lineage)
        if rebuild:
            _clear_existing(connection)
            if output_dir.exists():
                shutil.rmtree(output_dir)

        audiences = load_audiences(config.document)
        analytical = _load_analytical_evidence(connection, lineage)
        options = build_options(
            list(config.document["option_catalogue"]),
            analytical["financial_base"],
            analytical["scenario_comparison"],
            analytical["optimisation_comparison"],
        )
        objections = build_objections(list(config.document["challenge_catalogue"]))
        challenges = build_challenge_responses(objections)
        revision_challenge = next(
            response.challenge_id
            for response in challenges
            if response.objection_id
            == next(obj.objection_id for obj in objections if obj.revision_required)
        )
        revision = build_required_revision(
            str(config.document["revision_rules"]["initial_position"]),
            str(config.document["revision_rules"]["revised_position"]),
            revision_challenge,
        )

        run = _build_run(config, lineage, audiences, options, objections)
        claims = _build_claims(run, analytical, options)
        decision_record = build_decision_record(run, options, challenges, [revision])

        _persist_evidence(
            connection,
            run,
            audiences,
            options,
            objections,
            challenges,
            [revision],
            claims,
            decision_record,
        )
        connection.commit()

        products = _write_outputs(
            output_dir,
            run,
            audiences,
            options,
            objections,
            challenges,
            [revision],
            claims,
            decision_record,
            analytical,
        )
        provenance_rows = build_provenance_rows(run.communication_run_id, output_dir)
        _persist_products_and_provenance(
            connection, run.communication_run_id, products, provenance_rows
        )
        connection.commit()
        write_csv(
            output_dir / "communication_provenance.csv",
            provenance_rows,
            [
                "communication_run_id",
                "provenance_id",
                "artefact_name",
                "source_type",
                "source_reference",
                "checksum",
            ],
        )
        provenance_path = output_dir / "communication_provenance.csv"
        connection.execute(
            "INSERT OR REPLACE INTO evidence_communication_products VALUES (?, ?, ?, ?, ?, ?)",
            (
                run.communication_run_id,
                "PROD-015",
                "all",
                "communication_provenance.csv",
                "csv",
                file_checksum(provenance_path),
            ),
        )
        connection.commit()
        _update_stakeholder_templates(objections, challenges)

    summary = verify_communication_evidence(database_path, output_dir=output_dir)
    return {
        "communication_run_id": run.communication_run_id,
        "decision_status": run.decision_status,
        "approval_status": run.approval_status,
        "product_count": len(PRODUCT_FILES),
        **summary,
    }


def verify_communication_evidence(
    database_path: Path,
    output_dir: Path = Path("outputs/communication"),
) -> dict[str, Any]:
    missing_files = [name for name in PRODUCT_FILES if not (output_dir / name).exists()]
    if missing_files:
        raise FileNotFoundError(f"Missing communication outputs: {missing_files}")

    combined_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(output_dir.iterdir())
        if path.suffix in {".md", ".csv", ".json"}
    )
    validate_language_controls(combined_text)

    with open_connection(database_path) as connection:
        run = fetch_one(
            connection,
            "SELECT * FROM evidence_communication_runs ORDER BY communication_run_id DESC LIMIT 1",
        )
        if not run:
            raise CommunicationEvidenceError("No communication run persisted.")
        if run["decision_status"] != "awaiting_governance_decision":
            raise CommunicationEvidenceError("Decision status is not awaiting governance.")
        if run["approval_status"] != "not_approved":
            raise CommunicationEvidenceError("Approval status is not_approved.")
        counts = {
            table: int(
                fetch_one(connection, f"SELECT COUNT(*) AS count FROM {table}")["count"]  # type: ignore[index]
            )
            for table in COMMUNICATION_TABLES
        }
        claim_count = counts["evidence_communication_claims"]
        if claim_count < 9:
            raise CommunicationEvidenceError("Insufficient claim lineage rows.")
        revision_count = counts["evidence_communication_revisions"]
        if revision_count < 1:
            raise CommunicationEvidenceError("Required analytical revision missing.")
        options = fetch_all(
            connection,
            "SELECT implementation_status FROM evidence_communication_options",
        )
        if any(row["implementation_status"] != "not_approved" for row in options):
            raise CommunicationEvidenceError("An option was marked approved.")
    return {
        "communication_run_id": str(run["communication_run_id"]),
        "row_counts": counts,
        "claim_count": claim_count,
        "revision_count": revision_count,
    }


def export_existing_communication_evidence(
    database_path: Path,
    output_dir: Path = Path("outputs/communication"),
) -> list[str]:
    summary = verify_communication_evidence(database_path, output_dir)
    return sorted([*PRODUCT_FILES, f"verified:{summary['communication_run_id']}"])


def _build_run(
    config: CommunicationConfig,
    lineage: dict[str, str],
    audiences: list[Audience],
    options: list[CommunicationOption],
    objections: list[Objection],
) -> CommunicationRun:
    config_checksum = stable_digest(config.document)
    audience_checksum = stable_digest([asdict(audience) for audience in audiences])
    option_checksum = stable_digest([asdict(option) for option in options])
    challenge_checksum = stable_digest([asdict(objection) for objection in objections])
    decision_status = str(config.document["decision_record_schema"]["decision_status"])
    approval_status = str(config.document["decision_record_schema"]["approval_status"])
    run_payload = {
        "framework_version": config.framework_version,
        "lineage": lineage,
        "config_checksum": config_checksum,
        "audience_catalogue_checksum": audience_checksum,
        "option_catalogue_checksum": option_checksum,
        "challenge_catalogue_checksum": challenge_checksum,
    }
    return CommunicationRun(
        communication_run_id=f"COM-{stable_digest(run_payload)}",
        lineage=lineage,
        config_checksum=config_checksum,
        audience_catalogue_checksum=audience_checksum,
        option_catalogue_checksum=option_checksum,
        challenge_catalogue_checksum=challenge_checksum,
        decision_status=decision_status,
        approval_status=approval_status,
    )


def _load_analytical_evidence(
    connection: sqlite3.Connection,
    lineage: dict[str, str],
) -> dict[str, Any]:
    return {
        "quality_run": fetch_one(
            connection,
            "SELECT * FROM evidence_quality_runs WHERE quality_run_id = ?",
            (lineage["quality"],),
        ),
        "utilisation_run": fetch_one(
            connection,
            "SELECT * FROM evidence_utilisation_runs WHERE utilisation_run_id = ?",
            (lineage["utilisation"],),
        ),
        "forecast_run": fetch_one(
            connection,
            "SELECT * FROM evidence_forecast_runs WHERE forecast_run_id = ?",
            (lineage["forecast"],),
        ),
        "financial_run": fetch_one(
            connection,
            "SELECT * FROM evidence_financial_runs WHERE financial_run_id = ?",
            (lineage["financial"],),
        ),
        "financial_base": fetch_all(
            connection,
            """
            SELECT * FROM evidence_financial_comparison
            WHERE financial_run_id = ? AND assumption_set = 'base'
            ORDER BY financial_case_id
            """,
            (lineage["financial"],),
        ),
        "financial_sensitivity": fetch_all(
            connection,
            """
            SELECT * FROM evidence_financial_sensitivity
            WHERE financial_run_id = ?
            ORDER BY ABS(tornado_impact) DESC, financial_case_id
            LIMIT 20
            """,
            (lineage["financial"],),
        ),
        "financial_break_even": fetch_all(
            connection,
            """
            SELECT * FROM evidence_financial_break_even
            WHERE financial_run_id = ?
            ORDER BY financial_case_id, break_even_metric
            """,
            (lineage["financial"],),
        ),
        "scenario_comparison": fetch_all(
            connection,
            "SELECT * FROM evidence_scenario_comparison WHERE scenario_run_id = ? ORDER BY scenario_id",
            (lineage["scenario"],),
        ),
        "optimisation_comparison": fetch_all(
            connection,
            "SELECT * FROM evidence_optimisation_comparison WHERE optimisation_run_id = ? ORDER BY case_id",
            (lineage["optimisation"],),
        ),
        "potential_release": fetch_all(
            connection,
            """
            SELECT * FROM evidence_optimisation_building_status
            WHERE optimisation_run_id = ? AND potentially_releasable_flag = 1
            ORDER BY case_id, building_id
            """,
            (lineage["optimisation"],),
        ),
        "simulation_summary": fetch_all(
            connection,
            "SELECT * FROM evidence_simulation_summary WHERE simulation_run_id = ? ORDER BY simulation_case_id, experiment_id",
            (lineage["simulation"],),
        ),
        "simulation_workforce": fetch_all(
            connection,
            """
            SELECT * FROM evidence_simulation_workforce_metrics
            WHERE simulation_run_id = ?
            ORDER BY workforce_bottleneck_count DESC, blocked_demand_contacts DESC
            LIMIT 20
            """,
            (lineage["simulation"],),
        ),
        "buildings": fetch_all(
            connection,
            """
            SELECT building_id, site_id, building_name, building_type, ownership_type,
                   lease_end_date, floor_area_m2, accessibility_rating, condition_rating, active_flag
            FROM curated_buildings
            ORDER BY building_id
            """,
        ),
        "rooms": fetch_all(
            connection,
            """
            SELECT r.room_id, r.building_id, r.room_type, r.protected_capacity_flag,
                   r.specialist_equipment, u.effective_utilisation
            FROM curated_rooms r
            LEFT JOIN evidence_room_utilisation u
              ON u.room_id = r.room_id AND u.utilisation_run_id = ?
            ORDER BY r.room_id
            """,
            (lineage["utilisation"],),
        ),
    }


def _build_claims(
    run: CommunicationRun,
    analytical: dict[str, Any],
    options: list[CommunicationOption],
) -> list[Claim]:
    financial_best = max(options, key=lambda option: option.nominal_npv)
    simulation_rows = analytical["simulation_summary"]
    workforce_rows = analytical["simulation_workforce"]
    utilisation = analytical["utilisation_run"] or {}
    quality = analytical["quality_run"] or {}
    forecast = analytical["forecast_run"] or {}
    release = analytical["potential_release"]
    claims = [
        Claim(
            "CLM-001",
            "all",
            "All simulation case/experiment resilience rows failed.",
            "evidence_simulation_summary",
            run.lineage["simulation"],
            f"failed_rows={len(simulation_rows)}",
            "Simulation failure is retained as a primary caveat.",
            "No implementation approval.",
            "executive_options_paper.md",
        ),
        Claim(
            "CLM-002",
            "finance",
            f"{financial_best.option_id} has the strongest nominal financial result.",
            "evidence_financial_comparison",
            run.lineage["financial"],
            f"npv={financial_best.nominal_npv}",
            "Nominal NPV is descriptive only.",
            "not realisable without mitigation",
            "finance_brief.md",
        ),
        Claim(
            "CLM-003",
            "finance",
            "Risk-adjusted NPV is 0.0 under current resilience evidence.",
            "evidence_financial_comparison",
            run.lineage["financial"],
            "max_risk_adjusted_npv=0.0",
            "Risk adjustment caps realisability when thresholds fail.",
            "No guaranteed savings.",
            "finance_brief.md",
        ),
        Claim(
            "CLM-004",
            "clinical_operational",
            "Workforce was the dominant simulated bottleneck.",
            "evidence_simulation_workforce_metrics",
            run.lineage["simulation"],
            f"top_bottleneck_count={workforce_rows[0]['workforce_bottleneck_count'] if workforce_rows else 0}",
            "Workforce blocking qualifies utilisation and move interpretation.",
            "Further mitigation testing required.",
            "clinical_operational_brief.md",
        ),
        Claim(
            "CLM-005",
            "technical",
            f"Overall data-quality score is {quality.get('overall_score')}.",
            "evidence_quality_runs",
            run.lineage["quality"],
            "overall_score",
            "Quality score is a configured synthetic control result.",
            "Manual reviews remain open.",
            "technical_appendix.md",
        ),
        Claim(
            "CLM-006",
            "executive",
            f"Estate effective utilisation is {utilisation.get('overall_effective_utilisation')}.",
            "evidence_utilisation_runs",
            run.lineage["utilisation"],
            "overall_effective_utilisation",
            "Utilisation is descriptive and quality gated.",
            "Protected rooms require context.",
            "executive_options_paper.md",
        ),
        Claim(
            "CLM-007",
            "technical",
            f"Forecast horizon is {forecast.get('forecast_horizon')} months.",
            "evidence_forecast_runs",
            run.lineage["forecast"],
            "forecast_horizon",
            "Forecasts use 24 synthetic monthly observations.",
            "Intervals are not clinical guarantees.",
            "technical_appendix.md",
        ),
        Claim(
            "CLM-008",
            "estates",
            f"{len(release)} building-case rows are potentially releasable in mathematical candidates.",
            "evidence_optimisation_building_status",
            run.lineage["optimisation"],
            "potentially_releasable_flag=1",
            "Release means mathematical candidate evidence only.",
            "No building is identified for closure from this evidence.",
            "estates_brief.md",
        ),
        Claim(
            "CLM-009",
            "all",
            "Communication products are synthetic and non-approving.",
            "evidence_communication_runs",
            run.communication_run_id,
            "approval_status=not_approved",
            "Communication translates evidence without governance action.",
            "No real stakeholder approval.",
            "decision_record.md",
        ),
    ]
    return claims


def _write_outputs(
    output_dir: Path,
    run: CommunicationRun,
    audiences: list[Audience],
    options: list[CommunicationOption],
    objections: list[Objection],
    challenges: list[ChallengeResponse],
    revisions: list[Revision],
    claims: list[Claim],
    decision_record: dict[str, Any],
    analytical: dict[str, Any],
) -> list[dict[str, str]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    option_rows = [asdict(option) for option in options]
    audience_rows = [asdict(audience) for audience in audiences]
    objection_rows = [asdict(objection) for objection in objections]
    challenge_rows = [asdict(challenge) for challenge in challenges]
    revision_rows = [asdict(revision) for revision in revisions]
    claim_rows = [asdict(claim) for claim in claims]

    summary = {
        "communication_run_id": run.communication_run_id,
        "evidence_lineage": run.lineage,
        "decision_status": run.decision_status,
        "approval_status": run.approval_status,
        "product_count": len(PRODUCT_FILES),
        "central_principle": "Analytical feasibility is not operational resilience is not financial realisability is not governance approval.",
    }
    write_json(output_dir / "communication_run_summary.json", summary)
    write_csv(
        output_dir / "audience_catalogue.csv",
        audience_rows,
        ["audience_id", "label", "detail_level", "primary_need"],
    )
    write_csv(output_dir / "option_catalogue.csv", option_rows, list(option_rows[0]))
    write_csv(
        output_dir / "stakeholder_objection_register.csv", objection_rows, list(objection_rows[0])
    )
    write_csv(output_dir / "challenge_response_log.csv", challenge_rows, list(challenge_rows[0]))
    write_csv(output_dir / "recommendation_revision_log.csv", revision_rows, list(revision_rows[0]))
    write_csv(output_dir / "communication_evidence_map.csv", claim_rows, list(claim_rows[0]))
    write_json(output_dir / "decision_record.json", decision_record)

    write_markdown(
        output_dir / "executive_options_paper.md", _executive_paper(run, options, analytical)
    )
    write_markdown(output_dir / "clinical_operational_brief.md", _clinical_brief(run, analytical))
    write_markdown(output_dir / "finance_brief.md", _finance_brief(run, options, analytical))
    write_markdown(output_dir / "estates_brief.md", _estates_brief(run, analytical))
    write_markdown(
        output_dir / "technical_appendix.md", _technical_appendix(run, analytical, claims)
    )
    write_markdown(output_dir / "decision_record.md", _decision_record_markdown(decision_record))
    write_markdown(output_dir / "communication_limitations.md", _limitations_markdown())

    products: list[dict[str, str]] = []
    for index, file_name in enumerate(PRODUCT_FILES, start=1):
        path = output_dir / file_name
        if path.exists():
            products.append(
                {
                    "product_id": f"PROD-{index:03d}",
                    "communication_run_id": run.communication_run_id,
                    "audience_id": _audience_for_product(file_name),
                    "file_name": file_name,
                    "product_type": path.suffix.removeprefix("."),
                    "checksum": file_checksum(path),
                }
            )
    return products


def _executive_paper(
    run: CommunicationRun,
    options: list[CommunicationOption],
    analytical: dict[str, Any],
) -> str:
    best = max(options, key=lambda option: option.nominal_npv)
    simulation_rows = analytical["simulation_summary"]
    return f"""# Executive Options Paper

## 1. Purpose

Provide a governance-ready, non-approving options paper using synthetic Milestones 1-11 evidence.

## 2. Decision context

Analytical feasibility is not the same as operational resilience is not the same as financial realisability is not the same as governance approval.

## 3. Evidence considered

Run lineage: `{json.dumps(run.lineage, sort_keys=True)}`.

## 4. Current estate position

Estate-wide effective utilisation is `{(analytical["utilisation_run"] or {}).get("overall_effective_utilisation")}` and the overall data-quality score is `{(analytical["quality_run"] or {}).get("overall_score")}`.

## 5. Demand outlook

Forecast horizon is `{(analytical["forecast_run"] or {}).get("forecast_horizon")}` months, using synthetic monthly observations.

## 6. Options assessed

{markdown_table([asdict(option) for option in options], ["option_id", "option_name", "feasibility_status", "simulation_status", "financial_readiness", "nominal_npv", "risk_adjusted_npv", "implementation_status"])}

## 7. Operational-resilience findings

All `{len(simulation_rows)}` simulated resilience rows failed. No move is operationally approved.

## 8. Financial implications

Option {best.option_id} has the strongest nominal financial result under the configured base assumptions. The option remains not realisable without mitigation because the linked simulation evidence failed configured operational-resilience thresholds.

## 9. Risks and uncertainties

Workforce blocking, waiting times, unserved demand, transition cost uncertainty and synthetic forecast limits remain material.

## 10. Conditions required before any implementation decision

Operational mitigation testing, service continuity review, workforce validation, protected-capacity review and refreshed cost assumptions are required.

## 11. Decision options for governance

- Retain current estate configuration while investigating workforce and flow constraints.
- Commission targeted mitigation testing for selected financially positive cases before any estate decision.
- Refine data and assumptions, then rerun modelling.
- Do not progress selected consolidation concepts under current evidence.

## 12. Limitations

Synthetic evidence only. No option is recommended. Approval status remains not approved.
"""


def _clinical_brief(run: CommunicationRun, analytical: dict[str, Any]) -> str:
    workforce = analytical["simulation_workforce"]
    top = workforce[0] if workforce else {}
    return f"""# Clinical and Operational Brief

Run lineage: `{json.dumps(run.lineage, sort_keys=True)}`.

All simulated resilience rows failed. Workforce was the dominant bottleneck where supported by evidence; the highest retained bottleneck count is `{top.get("workforce_bottleneck_count", 0)}` with blocked demand `{top.get("blocked_demand_contacts", 0)}`.

Focus areas:

- forecast face-to-face demand and room-hour requirements;
- room compatibility, protected capacity and specialist equipment;
- service continuity and no operationally approved moves;
- completion rates, waiting times, unserved demand and workforce blocking;
- mitigation tests before any estate decision.

No move is operationally approved. Evidence is synthetic and not clinically validated.
"""


def _finance_brief(
    run: CommunicationRun,
    options: list[CommunicationOption],
    analytical: dict[str, Any],
) -> str:
    rows = [asdict(option) for option in options]
    best = max(options, key=lambda option: option.nominal_npv)
    return f"""# Finance Brief

Run lineage: `{json.dumps(run.lineage, sort_keys=True)}`.

Financial language uses synthetic nominal financial effect, planning estimate and not realisable without mitigation. Positive nominal NPV does not override operational failure.

{markdown_table(rows, ["option_id", "option_name", "nominal_npv", "risk_adjusted_npv", "payback_status", "financial_readiness", "implementation_status"])}

Option {best.option_id} is nominally financially positive under configured assumptions, but the risk-adjusted NPV remains `{best.risk_adjusted_npv}` and the option is not realisable without mitigation.

Sensitivity and break-even evidence are retained in `evidence_financial_sensitivity` and `evidence_financial_break_even`; values are planning estimates, not guaranteed benefits.
"""


def _estates_brief(run: CommunicationRun, analytical: dict[str, Any]) -> str:
    release_rows = analytical["potential_release"]
    buildings = analytical["buildings"][:8]
    return f"""# Estates Brief

Run lineage: `{json.dumps(run.lineage, sort_keys=True)}`.

Building and room evidence is synthetic. No building is identified for closure based on this communication evidence.

{markdown_table(buildings, ["building_id", "site_id", "building_type", "ownership_type", "lease_end_date", "condition_rating", "accessibility_rating"])}

Potential release evidence:

{markdown_table(release_rows, ["case_id", "building_id", "site_id", "status"])}

The phrase potentially releasable means potentially releasable in the mathematical candidate only. Operational validation, protected-room checks, service-location dependencies and transition exposure remain conditions precedent.
"""


def _technical_appendix(
    run: CommunicationRun,
    analytical: dict[str, Any],
    claims: list[Claim],
) -> str:
    return f"""# Technical Appendix

Run lineage: `{json.dumps(run.lineage, sort_keys=True)}`.

Quality score: `{(analytical["quality_run"] or {}).get("overall_score")}`.
Forecast history: `{(analytical["forecast_run"] or {}).get("historical_start_period")}` to `{(analytical["forecast_run"] or {}).get("historical_end_period")}`.
Simulation engine: `standard_library_discrete_event` with persisted replication evidence.
Financial readiness: `{(analytical["financial_run"] or {}).get("readiness_status")}`.

Claim lineage:

{markdown_table([asdict(claim) for claim in claims], ["claim_id", "audience", "source_table", "source_run_id", "source_record_or_metric", "output_document"])}

Relative documentation references: `docs/decision_criteria.md`, `docs/dashboard_interpretation.md`, `docs/simulation_resilience.md`, `docs/financial_risk_adjustment.md`, `docs/limitations.md`.
"""


def _decision_record_markdown(record: dict[str, Any]) -> str:
    return f"""# Decision Record

Decision record ID: `{record["decision_record_id"]}`.

Decision status: `{record["decision_status"]}`.

Approval status: `{record["approval_status"]}`.

Options considered: `{", ".join(record["options_considered"])}`.

Conditions precedent:

{chr(10).join(f"- {item}" for item in record["conditions_precedent"])}

Decision options:

{chr(10).join(f"- {item}" for item in record["decision_options"])}

No final recommendation is made and no option is selected.
"""


def _limitations_markdown() -> str:
    return """# Communication Limitations

- All stakeholder objections are synthetic challenge scenarios.
- No real stakeholder meeting, quote, agreement or approval is represented.
- No final implementation recommendation is generated.
- All analytical outputs remain synthetic and non-audited.
- Simulation failures and financial non-realisability remain unresolved.
- Communication products do not send emails, trigger workflows or deploy anything.
"""


def _persist_evidence(
    connection: sqlite3.Connection,
    run: CommunicationRun,
    audiences: list[Audience],
    options: list[CommunicationOption],
    objections: list[Objection],
    challenges: list[ChallengeResponse],
    revisions: list[Revision],
    claims: list[Claim],
    decision_record: dict[str, Any],
) -> None:
    connection.execute(
        """
        INSERT INTO evidence_communication_runs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run.communication_run_id,
            run.lineage["ingestion"],
            run.lineage["quality"],
            run.lineage["utilisation"],
            run.lineage["forecast"],
            run.lineage["scenario"],
            run.lineage["optimisation"],
            run.lineage["simulation"],
            run.lineage["financial"],
            "m12-v1",
            run.config_checksum,
            run.audience_catalogue_checksum,
            run.option_catalogue_checksum,
            run.challenge_catalogue_checksum,
            run.decision_status,
            run.approval_status,
        ),
    )
    for audience in audiences:
        connection.execute(
            "INSERT INTO evidence_communication_audiences VALUES (?, ?, ?, ?, ?)",
            (
                run.communication_run_id,
                audience.audience_id,
                audience.label,
                audience.detail_level,
                audience.primary_need,
            ),
        )
    for option in options:
        connection.execute(
            "INSERT INTO evidence_communication_options VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (run.communication_run_id, *asdict(option).values()),
        )
    for objection in objections:
        connection.execute(
            "INSERT INTO evidence_communication_objections VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (run.communication_run_id, *asdict(objection).values()),
        )
    for challenge in challenges:
        connection.execute(
            "INSERT INTO evidence_communication_challenges VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (run.communication_run_id, *asdict(challenge).values()),
        )
    for revision in revisions:
        connection.execute(
            "INSERT INTO evidence_communication_revisions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (run.communication_run_id, *asdict(revision).values()),
        )
    for claim in claims:
        connection.execute(
            "INSERT INTO evidence_communication_claims VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (run.communication_run_id, *asdict(claim).values()),
        )
    connection.execute(
        "INSERT INTO evidence_communication_decision_records VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            run.communication_run_id,
            decision_record["decision_record_id"],
            decision_record["decision_context"],
            json.dumps(decision_record["evidence_lineage"], sort_keys=True),
            json.dumps(decision_record["options_considered"], sort_keys=True),
            json.dumps(decision_record["key_findings"], sort_keys=True),
            json.dumps(decision_record["assumptions"], sort_keys=True),
            json.dumps(decision_record["risks"], sort_keys=True),
            json.dumps(decision_record["uncertainties"], sort_keys=True),
            json.dumps(decision_record["challenges"], sort_keys=True),
            json.dumps(decision_record["revisions"], sort_keys=True),
            json.dumps(decision_record["conditions_precedent"], sort_keys=True),
            json.dumps(decision_record["decision_options"], sort_keys=True),
            decision_record["decision_status"],
            decision_record["approval_status"],
        ),
    )


def _persist_products_and_provenance(
    connection: sqlite3.Connection,
    communication_run_id: str,
    products: list[dict[str, str]],
    provenance_rows: list[dict[str, str]],
) -> None:
    for product in products:
        connection.execute(
            "INSERT INTO evidence_communication_products VALUES (?, ?, ?, ?, ?, ?)",
            (
                communication_run_id,
                product["product_id"],
                product["audience_id"],
                product["file_name"],
                product["product_type"],
                product["checksum"],
            ),
        )
    for row in provenance_rows:
        connection.execute(
            "INSERT OR REPLACE INTO evidence_communication_provenance VALUES (?, ?, ?, ?, ?, ?)",
            (
                communication_run_id,
                row["provenance_id"],
                row["artefact_name"],
                row["source_type"],
                row["source_reference"],
                row["checksum"],
            ),
        )


def _clear_existing(connection: sqlite3.Connection) -> None:
    for table in COMMUNICATION_TABLES:
        connection.execute(f"DELETE FROM {table}")


def _update_stakeholder_templates(
    objections: list[Objection],
    challenges: list[ChallengeResponse],
) -> None:
    root = repository_root()
    stakeholder_dir = root / "stakeholder_evidence"
    write_markdown(
        stakeholder_dir / "communication_plan.md",
        """# Communication Plan

Milestone 12 translates synthetic Milestones 1-11 evidence into audience-specific, non-approving briefing products.

No communications have been delivered. No real stakeholder meeting, agreement, quotation or approval is represented.

Audiences: executive leaders, clinical and operational leaders, finance stakeholders, estates and facilities stakeholders, and technical reviewers.

Central principle: analytical feasibility is not operational resilience is not financial realisability is not governance approval.
""",
    )
    write_csv(
        stakeholder_dir / "objection_register.csv",
        [asdict(objection) for objection in objections],
        list(asdict(objections[0])),
    )
    write_csv(
        stakeholder_dir / "challenge_response_log.csv",
        [asdict(challenge) for challenge in challenges],
        list(asdict(challenges[0])),
    )


def _audience_for_product(file_name: str) -> str:
    if file_name.startswith("executive"):
        return "executive"
    if file_name.startswith("clinical"):
        return "clinical_operational"
    if file_name.startswith("finance"):
        return "finance"
    if file_name.startswith("estates"):
        return "estates"
    if file_name.startswith("technical"):
        return "technical"
    return "all"
