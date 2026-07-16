"""Stable optimisation constraint names and helpers."""


def demand_constraint(service_id: str, period: str) -> str:
    return f"demand__{service_id}__{period}"


def face_to_face_floor_constraint(service_id: str, period: str) -> str:
    return f"face_to_face_floor__{service_id}__{period}"


def remote_limit_constraint(service_id: str, period: str) -> str:
    return f"remote_limit__{service_id}__{period}"


def room_capacity_constraint(room_id: str, period: str) -> str:
    return f"room_capacity__{room_id}__{period}"


def room_activation_constraint(candidate_id: str) -> str:
    return f"room_activation__{candidate_id}"


def building_activation_constraint(room_id: str) -> str:
    return f"building_activation__{room_id}"


def move_activation_constraint(candidate_id: str) -> str:
    return f"move_activation__{candidate_id}"


def protected_room_constraint(room_id: str) -> str:
    return f"protected_room_retained__{room_id}"
