"""Validity rule helpers."""

from estate_intelligence.validation.rules import build_rule_catalogue


def validity_rules() -> list[str]:
    """Return enabled validity rule identifiers."""

    return [rule.rule_id for rule in build_rule_catalogue() if rule.dimension == "validity"]
