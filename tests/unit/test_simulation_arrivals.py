import random
from pathlib import Path

from estate_intelligence.simulation.arrivals import build_arrivals, reconciled_contact_count
from estate_intelligence.simulation.models import AllocationInput, ServiceInput, SimulationConfig
from estate_intelligence.simulation.service_times import sampled_duration


def test_arrivals_are_non_negative_and_reconciled() -> None:
    config = SimulationConfig.from_yaml(Path("config/simulation.yaml"))
    allocations = [
        AllocationInput(
            simulation_case_id="case",
            service_id="SVC-1",
            period="2026-04",
            room_id="ROOM-1",
            building_id="BLD-1",
            site_id="SITE-1",
            allocated_hours=12.0,
        )
    ]
    services = {
        "SVC-1": ServiceInput(
            service_id="SVC-1",
            service_name="Service",
            minimum_room_type="consultation",
            specialist_equipment_required="",
            remote_eligible_rate=0.0,
            average_duration_minutes=30.0,
        )
    }

    arrivals = build_arrivals(
        config=config,
        allocations=allocations,
        services=services,
        demand_multiplier=1.0,
        duration_multiplier=1.0,
        lateness_rng=random.Random(1),
        cancellation_rng=random.Random(2),
        no_show_rng=random.Random(3),
        duration_rng=random.Random(4),
        duration_fn=sampled_duration,
    )

    assert all(arrival.arrival_minute >= 0 for arrival in arrivals)
    assert len(arrivals) >= reconciled_contact_count(12.0 / 12, 30.0)
