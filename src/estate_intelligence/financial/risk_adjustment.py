"""Financial risk and confidence adjustments."""

from __future__ import annotations

from estate_intelligence.financial.models import FinanceConfig


def realisability_cap(config: FinanceConfig, simulation_status: str) -> float:
    if simulation_status == "fail":
        return config.simulation_risk_adjustments["failed_threshold_realisability_cap"]
    if simulation_status == "review_required":
        return config.simulation_risk_adjustments["review_required_realisability_cap"]
    return config.simulation_risk_adjustments["pass_realisability_cap"]


def readiness_status(npv: float, simulation_status: str, has_mitigation: bool) -> str:
    if simulation_status == "fail":
        return "not_realisable_without_mitigation" if has_mitigation else "review_required"
    if npv < 0:
        return "financially_negative"
    return "financially_positive"


def confidence_status(score: float, config: FinanceConfig, simulation_status: str) -> str:
    if simulation_status == "fail":
        return "not_realisable_without_mitigation"
    if score >= config.confidence_thresholds["high"]:
        return "high"
    if score >= config.confidence_thresholds["moderate"]:
        return "moderate"
    if score >= config.confidence_thresholds["low"]:
        return "low"
    return "insufficient_evidence"
