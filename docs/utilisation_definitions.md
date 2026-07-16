# Utilisation Definitions

- Available room hours: planned usable hours after excluding known closures, maintenance and protected downtime.
- Booked utilisation: booked room hours divided by available room hours.
- Actual occupied utilisation: observed occupied hours divided by available room hours.
- Attendance utilisation: attended clinical activity compared with booked or available capacity.
- Effective clinical utilisation: clinically productive occupied time after agreed exclusions.
- Peak utilisation: utilisation during the highest-demand periods.
- Persistent under-utilisation: sustained low use across an agreed review period.
- Protected specialist capacity: capacity deliberately retained for specialist services or equipment.
- Contingency capacity: capacity retained for resilience, disruption and demand shocks.

Milestone 5 implements these formulas in `src/estate_intelligence/metrics/`. Occupancy is proxied from completed,
non-cancelled, non-DNA booking sessions because no physical occupancy sensor data exists in the synthetic source.
