# Simulation Resilience

Resilience metrics include completion rate, waiting time, p95 waiting time, room occupancy, overtime, unserved contacts,
contingency remaining and threshold breach frequency.

Statuses are `pass`, `review_required` or `fail` at evidence level. A mathematically feasible optimisation allocation
can still fail simulation thresholds under operational stress. This is not a final recommendation.
## Financial Linkage

Milestone 10 consumes simulation resilience results directly. Failed thresholds trigger operational-resilience flags, mitigation costs and a `not_realisable_without_mitigation` financial readiness status.

Milestone 11 keeps simulation failure visible on executive, simulation and financial dashboard pages. The current dashboard states that all configured case/experiment resilience rows failed and highlights workforce as the dominant simulated bottleneck where supported by evidence.
