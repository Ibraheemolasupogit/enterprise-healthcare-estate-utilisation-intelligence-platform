"""Consistency rule helpers."""

from estate_intelligence.validation.rules import build_rule_catalogue


def consistency_rules() -> list[str]:
    """Return enabled consistency rule identifiers."""

    return [rule.rule_id for rule in build_rule_catalogue() if rule.dimension == "consistency"]
