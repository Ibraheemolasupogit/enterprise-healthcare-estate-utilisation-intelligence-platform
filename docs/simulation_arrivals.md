# Simulation Arrivals

Arrivals are generated from Milestone 8 allocated room hours and service duration assumptions. Monthly allocated
room-hours are converted into representative operational-day contacts using configured working days per month and the
simulation horizon.

The default process is scheduled deterministic arrival times with seeded lateness, cancellation and no-show streams.
Demand shocks are explicit experiment multipliers. Arrival counts are non-negative and stable for a fixed master seed,
case, experiment and replication.

The arrivals are synthetic operational contacts only. They do not represent patient identities or clinical pathways.
