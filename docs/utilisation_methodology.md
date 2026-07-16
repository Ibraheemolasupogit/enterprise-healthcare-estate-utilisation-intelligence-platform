# Utilisation Methodology

Milestone 5 calculates deterministic descriptive utilisation metrics over curated SQLite records that pass the
configured quality gate. Milestone 6 consumes this evidence for demand forecasting. Utilisation evidence still does
not define consolidation scenarios, optimise allocation or recommend estate changes.

## Analytical Grains

Metrics are produced by room, building, site, service, room-service, weekday, time band, month and room-month. Booking
metrics use booking records once at their native grain. Clinical activity metrics use monthly activity rows for contact
counts and are not joined back to individual bookings.

## Core Formulas

- available room hours = configured available hours per week x applicable weeks.
- booked utilisation = non-cancelled booked room hours / available room hours.
- actual occupied utilisation = completed attended booking hours / available room hours.
- attendance utilisation = actual attendance / planned attendance.
- contacts per occupied room hour = completed contacts / occupied room hours.

The configured analysis period is `2024-04-01` to `2026-03-31`. No closure calendar exists in the sample, so no
unobserved closure adjustment is invented.

## Booking Treatment

Cancelled bookings remain counted in scheduled-booking evidence but are excluded from the canonical booked-utilisation
numerator. Occupancy is proxied from completed, non-cancelled, non-DNA booking sessions. This is not sensor-measured
physical occupancy.
## Scenario Boundary

Milestone 7 consumes utilisation metrics as capacity and under-utilisation evidence. Utilisation metrics remain
descriptive; they do not by themselves approve room release, service relocation, savings, or operational change.
