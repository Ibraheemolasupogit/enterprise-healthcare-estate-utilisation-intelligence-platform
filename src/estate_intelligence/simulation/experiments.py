"""Experiment helpers for simulation evidence."""

from __future__ import annotations

from estate_intelligence.simulation.models import SimulationConfig, SimulationExperiment


def experiment_rows(
    simulation_run_id: str, experiments: list[SimulationExperiment]
) -> list[dict[str, object]]:
    return [
        {
            "simulation_run_id": simulation_run_id,
            "experiment_id": experiment.experiment_id,
            "label": experiment.label,
            "demand_multiplier": experiment.demand_multiplier,
            "workforce_multiplier": experiment.workforce_multiplier,
            "duration_multiplier": experiment.duration_multiplier,
            "specialist_room_capacity_multiplier": experiment.specialist_room_capacity_multiplier,
        }
        for experiment in experiments
    ]


def configured_experiments(config: SimulationConfig) -> list[SimulationExperiment]:
    return sorted(config.experiment_catalogue, key=lambda item: item.experiment_id)
