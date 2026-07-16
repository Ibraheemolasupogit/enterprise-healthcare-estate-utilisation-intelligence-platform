from pathlib import Path

import yaml

from estate_intelligence.validation.rules import DATASETS, DIMENSIONS, build_rule_catalogue

ROOT = Path(__file__).resolve().parents[2]


def test_data_quality_config_contract() -> None:
    document = yaml.safe_load((ROOT / "config" / "data_quality.yaml").read_text(encoding="utf-8"))

    assert document["contract_version"] == 1
    assert document["milestone_owner"] == "Milestone 4"
    assert tuple(document["enabled_dimensions"]) == DIMENSIONS
    assert set(document["intentional_defects"]) == {
        "DQ-0001",
        "DQ-0002",
        "DQ-0003",
        "DQ-0004",
        "DQ-0005",
    }


def test_data_quality_rule_contract() -> None:
    rules = build_rule_catalogue()

    assert {rule.dataset for rule in rules} == set(DATASETS)
    assert {rule.dimension for rule in rules} == set(DIMENSIONS)
    assert all(rule.milestone_owner == "Milestone 4" for rule in rules)
