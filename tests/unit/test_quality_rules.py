from collections import Counter

from estate_intelligence.validation.rules import DATASETS, DIMENSIONS, build_rule_catalogue


def test_rule_catalogue_covers_every_dataset_and_dimension() -> None:
    rules = build_rule_catalogue()

    assert len(rules) == len(DATASETS) * len(DIMENSIONS)
    assert Counter(rule.dataset for rule in rules) == {dataset: 7 for dataset in DATASETS}
    assert Counter(rule.dimension for rule in rules) == {dimension: 8 for dimension in DIMENSIONS}


def test_rule_catalogue_marks_known_defect_controls() -> None:
    rules = {rule.rule_id: rule for rule in build_rule_catalogue()}

    assert rules["DQ-ROM-UNI-001"].failure_action == "manual_review"
    assert rules["DQ-ROM-CMP-001"].failure_action == "accept_with_warning"
    assert rules["DQ-BKG-CON-001"].severity == "high"
    assert rules["DQ-FIN-CON-001"].severity == "high"
    assert rules["DQ-WRK-CON-001"].severity == "warning"
