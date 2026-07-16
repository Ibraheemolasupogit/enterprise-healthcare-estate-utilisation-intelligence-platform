from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIG_ROOT = ROOT / "config"
EXPECTED_CONFIG_KEYS = {
    "settings.yaml": {"contract_version", "milestone_owner", "purpose"},
    "data_contracts.yaml": {"contract_version", "milestone_owner", "future_sources"},
    "utilisation_thresholds.yaml": {"contract_version", "milestone_owner", "definitions"},
    "forecasting.yaml": {"contract_version", "milestone_owner", "framework_version"},
    "scenarios.yaml": {"contract_version", "milestone_owner", "framework_version"},
    "optimisation.yaml": {"contract_version", "milestone_owner", "framework_version"},
    "finance.yaml": {"contract_version", "milestone_owner", "finance"},
    "communication.yaml": {"contract_version", "milestone_owner", "framework_version"},
    "assurance.yaml": {"contract_version", "milestone_owner", "framework_version"},
    "portfolio.yaml": {"contract_version", "milestone_owner", "framework_version"},
    "risk_thresholds.yaml": {"contract_version", "milestone_owner", "risk_thresholds"},
    "synthetic_data.yaml": {"contract_version", "milestone_owner", "generation"},
    "database.yaml": {"contract_version", "milestone_owner", "engine"},
    "data_quality.yaml": {"contract_version", "milestone_owner", "enabled_dimensions"},
    "utilisation.yaml": {"contract_version", "milestone_owner", "framework_version"},
}
ENVIRONMENT_NAMES = {"development", "staging", "production"}
SECRET_MARKERS = {"password", "secret", "token", "apikey", "api_key", "credential"}
EVIDENCE_MARKERS = {"real saving", "approved decision", "patient record", "nhs number"}


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        document = yaml.safe_load(handle)
    assert isinstance(document, dict)
    return document


def test_all_yaml_contracts_parse_and_have_expected_keys() -> None:
    for filename, keys in EXPECTED_CONFIG_KEYS.items():
        document = load_yaml(CONFIG_ROOT / filename)
        assert keys.issubset(document.keys())
        assert document["milestone_owner"] in {
            "Milestone 1",
            "Milestone 2",
            "Milestone 3",
            "Milestone 4",
            "Milestone 5",
            "Milestone 6",
            "Milestone 7",
            "Milestone 8",
            "Milestone 9",
            "Milestone 10",
            "Milestone 11",
            "Milestone 12",
            "Milestone 13",
            "Milestone 14",
        }


def test_data_contract_lists_future_dataset_names_only() -> None:
    document = load_yaml(CONFIG_ROOT / "data_contracts.yaml")

    assert set(document["future_sources"]) == {
        "buildings",
        "rooms",
        "services",
        "bookings",
        "clinical_activity",
        "workforce",
        "finance",
        "accessibility",
    }
    assert "records" not in document


def test_environment_contract_names_are_valid() -> None:
    for environment in ENVIRONMENT_NAMES:
        document = load_yaml(CONFIG_ROOT / "environments" / f"{environment}.yaml")
        assert document["environment"] == environment
        assert document["environment"] in ENVIRONMENT_NAMES
        assert document["runtime"]["synthetic_data_only"] is True


def test_configuration_contracts_contain_no_obvious_secrets() -> None:
    for path in CONFIG_ROOT.rglob("*.yaml"):
        lowered = path.read_text(encoding="utf-8").lower()
        for marker in SECRET_MARKERS:
            assert f"{marker}:" not in lowered
            assert f"{marker}=" not in lowered


def test_configuration_contracts_do_not_claim_generated_evidence() -> None:
    for path in CONFIG_ROOT.rglob("*.yaml"):
        lowered = path.read_text(encoding="utf-8").lower()
        for marker in EVIDENCE_MARKERS:
            assert marker not in lowered
