# Simulation Methodology

Milestone 9 adds deterministic operational capacity and room-flow simulation over synthetic estate evidence. It tests
whether scenario and optimisation allocations remain operationally resilient when demand, contact duration,
cancellations, no-shows, workforce absence and room contention vary under configured assumptions.

The engine is a standard-library discrete-event simulator using a stable heap-ordered event queue. The time unit is
minutes and the simulation grain is representative service-room operational days derived from forecast monthly demand
and upstream allocation evidence.

Cases are resolved from evidence: current estate, light consolidation, flexible-room optimisation and hybrid
optimisation. Run identity includes upstream run IDs, config checksum, allocation checksum, experiment checksum, seed
strategy and engine identity.

Outputs are simulation evidence only. They do not approve estate change, make a final recommendation, or calculate NPV
or payback.
