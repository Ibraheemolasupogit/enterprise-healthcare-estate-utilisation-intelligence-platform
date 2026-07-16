"""Optimisation diagnostic helpers."""


def is_material_unmet_demand(value: float) -> bool:
    return value > 1e-6
