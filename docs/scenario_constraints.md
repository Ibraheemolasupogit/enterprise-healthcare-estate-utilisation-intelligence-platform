# Scenario Constraints

Scenario constraints cover room type, capacity, specialist equipment, protected capacity, forecast capacity,
contingency capacity, workforce feasibility, accessibility and service continuity.

Compatibility statuses include `compatible`, `incompatible_room_type`, `incompatible_capacity`,
`missing_equipment` and `protected_capacity_conflict`. Critical failures make a scenario infeasible. Warnings remain
warnings and require manual review.

No service is moved into an incompatible room by this milestone.

Milestone 8 uses these constraints as part of candidate eligibility and solver constraints. Incompatible scenario
candidates remain visible as audit evidence and are not silently forced into the solver.
