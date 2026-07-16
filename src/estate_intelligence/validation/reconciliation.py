"""Reconciliation rule helpers."""

from estate_intelligence.validation.rules import build_rule_catalogue


def reconciliation_rules() -> list[str]:
    """Return enabled reconciliation rule identifiers."""

    return [rule.rule_id for rule in build_rule_catalogue() if rule.dimension == "reconciliation"]
