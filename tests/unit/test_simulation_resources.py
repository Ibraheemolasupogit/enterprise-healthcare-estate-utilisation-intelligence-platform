from estate_intelligence.simulation.models import Arrival, RoomInput
from estate_intelligence.simulation.resources import RoomResource, WorkforceResource


def test_room_resource_enforces_fifo_wait_and_overtime() -> None:
    room = RoomInput(
        room_id="ROOM-1",
        building_id="BLD-1",
        site_id="SITE-1",
        room_type="consultation",
        capacity=4,
        specialist_equipment="",
        protected_capacity_flag=False,
        specialist_flag=False,
        opening_minute=480,
        closing_minute=540,
    )
    resource = RoomResource(room)
    first = Arrival(
        sequence=1,
        service_id="SVC-1",
        room_id="ROOM-1",
        arrival_minute=480,
        duration_minutes=45,
        cancelled=False,
        no_show=False,
    )
    second = first.model_copy(update={"sequence": 2, "arrival_minute": 490})

    assert resource.assign(first, 0.0, first.duration_minutes) == (480, 525)
    start, finish = resource.assign(second, 0.0, second.duration_minutes)

    assert start == 525
    assert finish == 570
    assert resource.contention_events == 1
    assert resource.overtime_minutes == 30


def test_workforce_resource_blocks_after_capacity() -> None:
    resource = WorkforceResource("SVC-1", capacity_contacts=1)

    assert resource.request() is True
    assert resource.request() is False
    assert resource.blocked_contacts == 1
