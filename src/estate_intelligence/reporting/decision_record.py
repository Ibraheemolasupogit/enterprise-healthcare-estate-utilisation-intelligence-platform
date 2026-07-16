"""Decision-record construction."""

from __future__ import annotations

from typing import Any

from estate_intelligence.reporting.models import (
    ChallengeResponse,
    CommunicationOption,
    CommunicationRun,
    Revision,
)


def build_decision_record(
    run: CommunicationRun,
    options: list[CommunicationOption],
    challenges: list[ChallengeResponse],
    revisions: list[Revision],
) -> dict[str, Any]:
    return {
        "decision_record_id": f"DR-{run.communication_run_id}",
        "communication_run_id": run.communication_run_id,
        "decision_context": (
            "Synthetic governance evidence for whether to request further validation, mitigation "
            "testing or modelling refinement."
        ),
        "evidence_lineage": run.lineage,
        "options_considered": [option.option_id for option in options],
        "key_findings": [
            "Analytical feasibility is not operational resilience.",
            "All configured simulation case/experiment resilience rows failed.",
            "Positive nominal NPV does not create financial realisability.",
            "Risk-adjusted NPV is 0.0 under current simulation evidence.",
        ],
        "assumptions": [
            "All evidence is synthetic and non-audited.",
            "No real stakeholder meeting, approval or quotation is represented.",
            "Communication products translate persisted evidence without changing it.",
        ],
        "risks": [
            "Workforce bottlenecks may prevent operational delivery.",
            "Transition and mitigation costs may change after real validation.",
            "Patient access and service continuity require local review.",
        ],
        "uncertainties": [
            "Forecasts use only 24 synthetic monthly observations.",
            "Simulation is simplified and not clinically validated.",
            "Financial values are planning estimates, not guaranteed benefits.",
        ],
        "challenges": [challenge.challenge_id for challenge in challenges],
        "revisions": [revision.revision_id for revision in revisions],
        "conditions_precedent": [
            "Resolve or mitigate failed simulation thresholds.",
            "Validate workforce capacity and service-flow assumptions.",
            "Review protected specialist capacity and access impacts.",
            "Refresh financial assumptions after operational mitigation testing.",
        ],
        "decision_options": [
            "Retain current estate configuration while investigating workforce and flow "
            "constraints.",
            "Commission targeted mitigation testing for selected financially positive cases "
            "before any estate decision.",
            "Refine data and assumptions, then rerun modelling.",
            "Do not progress selected consolidation concepts under current evidence.",
        ],
        "decision_status": run.decision_status,
        "approval_status": run.approval_status,
    }
