"""Synthetic objection and challenge-response construction."""

from __future__ import annotations

from typing import Any

from estate_intelligence.reporting.models import ChallengeResponse, Objection, Revision


def build_objections(challenge_catalogue: list[dict[str, Any]]) -> list[Objection]:
    objections: list[Objection] = []
    for index, row in enumerate(challenge_catalogue, start=1):
        objection_id = f"OBJ-{index:03d}"
        summary = str(row["objection_summary"])
        supported = summary in {
            "Staffing shortages distort current utilisation.",
            "Specialist capacity cannot be released safely.",
            "Transition costs may be incomplete.",
            "Positive NPV may be overstated.",
            "Mathematical feasibility does not prove operational deliverability.",
            "Simulation assumptions may not reflect real service flow.",
        }
        objections.append(
            Objection(
                objection_id=objection_id,
                stakeholder_group=str(row["stakeholder_group"]),
                objection_summary=summary,
                evidence_required=str(row["evidence_required"]),
                source_evidence="Milestones 4-11 persisted evidence and dashboard interpretation",
                status="supported" if supported else "partially_supported",
                analysis_response=(
                    "The concern is retained in the decision record and briefing caveats."
                ),
                decision_impact=(
                    "Requires governance review before any implementation decision; no option "
                    "is selected."
                ),
                revision_required=1
                if summary == "Mathematical feasibility does not prove operational deliverability."
                else 0,
            )
        )
    return objections


def build_challenge_responses(objections: list[Objection]) -> list[ChallengeResponse]:
    responses: list[ChallengeResponse] = []
    for index, objection in enumerate(objections, start=1):
        responses.append(
            ChallengeResponse(
                challenge_id=f"CHG-{index:03d}",
                objection_id=objection.objection_id,
                support_status=objection.status,
                evidence_considered=objection.source_evidence,
                analytical_response=(
                    "Current evidence is used to qualify the relevant claim rather than dismiss "
                    "the challenge."
                ),
                conclusion_change=(
                    "Analytical interpretation revised."
                    if objection.revision_required
                    else "No final governance conclusion is created."
                ),
                unresolved_concern=(
                    "Operational validation remains required with real local stakeholders and data."
                ),
            )
        )
    return responses


def build_required_revision(
    initial_position: str,
    revised_position: str,
    challenge_id: str,
) -> Revision:
    return Revision(
        revision_id="REV-001",
        initial_position=initial_position,
        challenge_id=challenge_id,
        evidence_considered=(
            "Simulation resilience rows all failed; completion rates were low, waits were high, "
            "workforce blocking and unserved demand persisted, and financial risk-adjusted "
            "NPV was 0.0."
        ),
        revised_position=revised_position,
        reason_for_change=(
            "Positive nominal NPV and payback were outweighed by failed operational resilience "
            "for realisability interpretation."
        ),
        affected_outputs=(
            "executive_options_paper.md; finance_brief.md; decision_record.md; "
            "communication_evidence_map.csv"
        ),
        status="complete",
    )
