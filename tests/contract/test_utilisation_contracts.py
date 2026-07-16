from pathlib import Path

import yaml

from estate_intelligence.metrics.models import UtilisationConfig
from estate_intelligence.metrics.reporting import METRIC_CATALOGUE

ROOT = Path(__file__).resolve().parents[2]


def test_utilisation_config_contract() -> None:
    config = UtilisationConfig.from_yaml(ROOT / "config" / "utilisation.yaml")

    assert config.milestone_owner == "Milestone 5"
    assert config.framework_version == "m5-v1"
    assert config.quality_policy.manual_review["high"] == "exclude"
    assert sum(config.formula_weights.values()) == 1.0


def test_utilisation_threshold_contract() -> None:
    document = yaml.safe_load(
        (ROOT / "config" / "utilisation_thresholds.yaml").read_text(encoding="utf-8")
    )

    assert document["milestone_owner"] == "Milestone 5"
    assert document["thresholds"]["persistent_under_utilisation"] == 0.35


def test_metric_catalogue_contains_required_formulas() -> None:
    formula_ids = {row["formula_id"] for row in METRIC_CATALOGUE}

    assert {
        "available_room_hours",
        "booked_utilisation",
        "actual_occupied_utilisation",
        "attendance_utilisation",
        "effective_clinical_utilisation",
        "persistent_under_utilisation",
        "unit_cost",
    }.issubset(formula_ids)
