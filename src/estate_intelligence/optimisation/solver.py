"""SciPy/HiGHS solver wrapper for Milestone 8 optimisation."""

from __future__ import annotations

from importlib import metadata
from typing import Any


def solver_version() -> str:
    try:
        return metadata.version("scipy")
    except metadata.PackageNotFoundError:
        return "not_installed"


def solver_identity(config_solver: str, threads: int, time_limit: int, mip_gap: float) -> str:
    return (
        f"{config_solver}|scipy={solver_version()}|threads={threads}|"
        f"time_limit={time_limit}|mip_gap={mip_gap}|method=highs"
    )


def scipy_milp_components() -> tuple[Any, Any, Any, Any]:
    try:
        from scipy.optimize import Bounds, LinearConstraint, milp  # type: ignore[import-untyped]
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "SciPy with optimize.milp is required for Milestone 8 optimisation."
        ) from exc
    return milp, LinearConstraint, Bounds, metadata.version("scipy")


def map_solver_status(native_status: str, unmet_demand: float) -> str:
    if native_status == "optimal":
        return "feasible_with_slack" if unmet_demand > 1e-6 else "optimal"
    if native_status == "infeasible":
        return "infeasible"
    if native_status == "unbounded":
        return "unbounded"
    if native_status == "time_limit":
        return "time_limit_without_solution"
    if native_status == "not_run":
        return "not_run"
    return "solver_error"


def native_status_name(status: int) -> str:
    return {
        0: "optimal",
        1: "time_limit",
        2: "infeasible",
        3: "unbounded",
        4: "solver_error",
    }.get(status, "solver_error")
