# Optimisation Solver

Milestone 8 uses SciPy `optimize.milp` with the open-source HiGHS MILP backend. No commercial solver is required.

Solver configuration is deterministic: one thread, fixed MIP gap, bounded solve time and stable variable and constraint
names. Solver identity records SciPy version and configured solve settings.

Native solver statuses are mapped to explicit evidence statuses including `optimal`, `feasible_with_slack`,
`infeasible`, `unbounded`, `solver_error` and time-limit states.

If SciPy with `optimize.milp` is unavailable, the command fails as a solver-system failure rather than falling back to
an unconstrained heuristic.
