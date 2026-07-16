from pathlib import Path

import pytest

from estate_intelligence.simulation.engine import _case_checksum_payload
from estate_intelligence.simulation.models import AllocationInput, SimulationCase, SimulationConfig


def test_simulation_config_validates_contract() -> None:
    config = SimulationConfig.from_yaml(Path("config/simulation.yaml"))

    assert config.milestone_owner == "Milestone 9"
    assert config.time_unit == "minutes"
    assert config.replications == 30
    assert len(config.experiment_catalogue) == 6


def test_simulation_config_rejects_non_fifo_queue(tmp_path: Path) -> None:
    payload = (
        Path("config/simulation.yaml")
        .read_text()
        .replace('queue_discipline: "fifo"', 'queue_discipline: "priority"')
    )
    config_path = tmp_path / "bad.yaml"
    config_path.write_text(payload)

    with pytest.raises(ValueError, match="fifo"):
        SimulationConfig.from_yaml(config_path)


def test_case_checksum_payload_sorts_active_room_ids() -> None:
    allocations = [
        AllocationInput(
            simulation_case_id="case_a",
            service_id="svc_1",
            period="2025-01",
            room_id="room_b",
            building_id="building_1",
            site_id="site_1",
            allocated_hours=10.0,
            remote_hours=1.0,
        )
    ]

    first = SimulationCase(
        simulation_case_id="case_a",
        source_type="optimisation",
        source_case_id="current_estate",
        label="Current estate",
        allocations=allocations,
        active_room_ids={"room_b", "room_a"},
    )
    second = first.model_copy(update={"active_room_ids": {"room_a", "room_b"}})

    assert _case_checksum_payload([first]) == _case_checksum_payload([second])
