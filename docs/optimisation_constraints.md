# Optimisation Constraints

Demand satisfaction is enforced as an exact service-period balance: allocated room hours plus permitted remote hours
plus configured unmet-demand slack must equal planning demand.

Face-to-face floor constraints preserve a configured minimum face-to-face share of fulfilled demand. When unmet-demand
slack is disabled in configuration, the slack variable is bounded to zero and genuinely impossible cases are reported as
infeasible.

Room-capacity constraints limit allocations to active compatible room capacity after configured buffer and contingency
capacity are retained.

Room activation constraints prevent allocation to inactive rooms. Building activation constraints require a building
to be active when any room in it is active.

Protected specialist rooms are fixed active. Specialist equipment, room type, room capacity, confidentiality,
co-location, workforce and accessibility checks are enforced before candidates enter the solver.

Infeasible or blocked candidate conditions are written as deterministic diagnostics rather than silently corrected.
