# Optimisation Methodology

Milestone 8 adds deterministic constrained allocation optimisation over synthetic estate evidence. It allocates
service-month forecast room-hour demand to eligible rooms using curated estate data, utilisation evidence, forecast
uncertainty and Milestone 7 scenario compatibility evidence.

The allocation grain is service by forecast month by receiving room. Candidate assignments are built from active
quality-gated rooms, service room requirements, protected-capacity rules, workforce evidence, accessibility evidence,
co-location and confidentiality rules.

The optimisation cases are current-estate, flexible-room, flexible-site and hybrid allocation. They are mathematical
cases only and are not implementation recommendations.

Demand is balanced exactly in each service-period. Unmet demand is represented as a high-penalty diagnostic slack
variable unless configuration explicitly prohibits it, in which case impossible cases remain solver-infeasible and are
written to infeasibility evidence.

Run identity and exports are deterministic. No runtime timestamp, solver log or absolute path is used in canonical
evidence.

The optimisation layer does not alter source, staging or curated data and does not approve estate change.

Milestone 9 consumes optimisation allocation evidence for operational simulation. Mathematical feasibility remains
distinct from simulated operational resilience.
