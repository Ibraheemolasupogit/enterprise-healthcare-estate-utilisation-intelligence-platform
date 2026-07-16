# Analytical Population

Milestone 5 derives its analytical population from curated records and Milestone 4 quality evidence.

Included records have `accepted` or `accepted_with_warning` status according to configuration. Manual-review records are
excluded by default. Child booking and activity rows are also excluded when their room is excluded.

Canonical handling:

- `ROOM-0002` and `ROOM-0026`: excluded from room-level analytics because of `DQ-ROM-UNI-001`.
- `BOOK-000025`: excluded because of high-severity attendance consistency review.
- `FIN-00002`: excluded from unit-cost metrics because of finance reconciliation review.
- `ROOM-0018`: retained with warning for missing optional specialist equipment.
- `WRK-00007`: retained with warning for available FTE above planned FTE.

Every exclusion is written to `analytics_population_exclusions.csv`.

