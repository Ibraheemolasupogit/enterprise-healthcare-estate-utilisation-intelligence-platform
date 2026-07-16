"""Stable optimisation variable names."""


def allocation_variable(candidate_id: str) -> str:
    return f"x__{candidate_id}"


def room_active_variable(room_id: str) -> str:
    return f"y__{room_id}"


def building_active_variable(building_id: str) -> str:
    return f"z__{building_id}"


def service_move_variable(service_id: str, source_site_id: str, target_site_id: str) -> str:
    return f"m__{service_id}__{source_site_id}__{target_site_id}"


def unmet_demand_variable(service_id: str, period: str) -> str:
    return f"u__{service_id}__{period}"


def remote_variable(service_id: str, period: str) -> str:
    return f"r__{service_id}__{period}"
