"""Scenario compatibility and constraint helpers."""

from collections.abc import Mapping

ROOM_TYPE_ORDER = {
    "consultation": 1,
    "treatment": 2,
    "diagnostic": 3,
    "specialist": 4,
    "group": 5,
    "training": 6,
}


def room_compatibility(
    service: Mapping[str, object], room: Mapping[str, object]
) -> tuple[str, str]:
    """Assess service-room compatibility with transparent reasons."""

    if str(room["active_flag"]).lower() != "true":
        return "incompatible_room_type", "room is inactive"
    minimum_type = str(service["minimum_room_type"])
    room_type = str(room["room_type"])
    if ROOM_TYPE_ORDER.get(room_type, 0) < ROOM_TYPE_ORDER.get(minimum_type, 0):
        return "incompatible_room_type", f"room type {room_type} below {minimum_type}"
    if int(str(room["capacity"])) < int(str(service["minimum_capacity"])):
        return "incompatible_capacity", "room capacity below service minimum"
    required = str(service["specialist_equipment_required"] or "")
    equipment = str(room["specialist_equipment"] or "")
    if required and required not in equipment:
        return "missing_equipment", "required specialist equipment absent"
    if str(room["protected_capacity_flag"]).lower() == "true" and minimum_type not in {
        "diagnostic",
        "specialist",
    }:
        return "protected_capacity_conflict", "protected capacity reserved for specialist use"
    return "compatible", "configured room rules satisfied"


def feasibility_from_constraints(rows: list[dict[str, object]]) -> str:
    """Derive scenario feasibility from constraint rows."""

    critical_failures = [
        row
        for row in rows
        if int(str(row["critical_flag"])) == 1 and str(row["result_status"]) == "fail"
    ]
    if critical_failures:
        return "infeasible"
    warnings = [row for row in rows if str(row["result_status"]) == "warning"]
    return "feasible_with_warnings" if warnings else "feasible"
