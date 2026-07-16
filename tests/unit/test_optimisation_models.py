from pathlib import Path

import pytest

from estate_intelligence.optimisation.models import Candidate, OptimisationConfig


def test_optimisation_config_validates_cases_and_coefficients() -> None:
    config = OptimisationConfig.from_yaml(Path("config/optimisation.yaml"))

    assert config.framework_version == "m8-v1"
    assert [case.case_id for case in config.optimisation_cases] == [
        "current_estate",
        "flexible_room",
        "flexible_site",
        "hybrid",
    ]
    assert all(value >= 0 for value in config.objective_weights.values())
    assert all(value >= 0 for value in config.cost_coefficients.values())


def test_optimisation_config_rejects_negative_coefficients() -> None:
    payload = OptimisationConfig.from_yaml(Path("config/optimisation.yaml")).model_dump()
    payload["cost_coefficients"]["unmet_demand_penalty_per_hour"] = -1

    with pytest.raises(ValueError):
        OptimisationConfig.model_validate(payload)


def test_candidate_eligibility_property() -> None:
    candidate = Candidate(
        candidate_id="CAND__SVC-001__2026-04__ROOM-0001",
        service_id="SVC-001",
        source_site_id="SITE-01",
        target_site_id="SITE-01",
        target_building_id="BLD-001",
        target_room_id="ROOM-0001",
        period="2026-04",
        planning_demand_hours=1.0,
        compatible_capacity_hours=10.0,
        room_type_compatible=True,
        equipment_compatible=True,
        capacity_compatible=True,
        accessibility_compatible=True,
        workforce_compatible=True,
        co_location_compatible=True,
        confidentiality_compatible=True,
        protected_capacity_effect="none",
        travel_penalty=0.0,
        relocation_penalty=0.0,
        disruption_penalty=0.0,
        candidate_status="eligible",
        exclusion_reason="",
    )

    assert candidate.is_eligible is True
