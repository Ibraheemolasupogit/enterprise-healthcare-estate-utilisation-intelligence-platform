from estate_intelligence.optimisation.variables import (
    allocation_variable,
    building_active_variable,
    remote_variable,
    room_active_variable,
    service_move_variable,
    unmet_demand_variable,
)


def test_variable_names_are_stable() -> None:
    assert allocation_variable("CAND-1") == "x__CAND-1"
    assert room_active_variable("ROOM-1") == "y__ROOM-1"
    assert building_active_variable("BLD-1") == "z__BLD-1"
    assert service_move_variable("SVC-1", "SITE-1", "SITE-2") == "m__SVC-1__SITE-1__SITE-2"
    assert unmet_demand_variable("SVC-1", "2026-04") == "u__SVC-1__2026-04"
    assert remote_variable("SVC-1", "2026-04") == "r__SVC-1__2026-04"
