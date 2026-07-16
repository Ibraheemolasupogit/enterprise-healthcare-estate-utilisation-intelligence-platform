import random
from pathlib import Path

from estate_intelligence.simulation.models import ServiceInput, SimulationConfig
from estate_intelligence.simulation.service_times import sampled_duration


def test_service_times_are_positive_and_capped() -> None:
    config = SimulationConfig.from_yaml(Path("config/simulation.yaml"))
    service = ServiceInput(
        service_id="SVC-1",
        service_name="Diagnostic",
        minimum_room_type="diagnostic",
        specialist_equipment_required="ultrasound",
        remote_eligible_rate=0.0,
        average_duration_minutes=45.0,
    )

    values = [sampled_duration(config, service, 1.35, random.Random(index)) for index in range(10)]
    cap = config.service_time_distributions["cap_minutes"]
    assert isinstance(cap, int | float | str)

    assert min(values) > 0
    assert max(values) <= float(cap)
