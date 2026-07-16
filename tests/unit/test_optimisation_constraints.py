from estate_intelligence.optimisation.constraints import (
    demand_constraint,
    protected_room_constraint,
    room_capacity_constraint,
)


def test_constraint_names_are_stable() -> None:
    assert demand_constraint("SVC-001", "2026-04") == "demand__SVC-001__2026-04"
    assert room_capacity_constraint("ROOM-0001", "2026-04") == ("room_capacity__ROOM-0001__2026-04")
    assert protected_room_constraint("ROOM-0001") == "protected_room_retained__ROOM-0001"
