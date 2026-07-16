from estate_intelligence.scenarios.constraints import (
    feasibility_from_constraints,
    room_compatibility,
)


def test_room_compatibility_preserves_specialist_rules() -> None:
    service = {
        "minimum_room_type": "diagnostic",
        "minimum_capacity": "4",
        "specialist_equipment_required": "ultrasound",
    }
    room = {
        "active_flag": "true",
        "room_type": "consultation",
        "capacity": "6",
        "specialist_equipment": "",
        "protected_capacity_flag": "false",
    }
    status, _ = room_compatibility(service, room)
    assert status == "incompatible_room_type"


def test_critical_constraint_failure_makes_scenario_infeasible() -> None:
    rows = [{"critical_flag": 1, "result_status": "fail"}]
    assert feasibility_from_constraints(rows) == "infeasible"
