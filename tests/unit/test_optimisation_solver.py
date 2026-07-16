from estate_intelligence.optimisation.solver import map_solver_status, solver_identity


def test_solver_status_mapping_preserves_unmet_demand() -> None:
    assert map_solver_status("optimal", 0.0) == "optimal"
    assert map_solver_status("optimal", 0.1) == "feasible_with_slack"
    assert map_solver_status("infeasible", 0.0) == "infeasible"
    assert map_solver_status("unbounded", 0.0) == "unbounded"


def test_solver_identity_includes_deterministic_settings() -> None:
    identity = solver_identity("scipy_milp_highs", threads=1, time_limit=20, mip_gap=0.0)

    assert "scipy_milp_highs" in identity
    assert "method=highs" in identity
    assert "threads=1" in identity
    assert "time_limit=20" in identity
