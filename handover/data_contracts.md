# Data Contracts

The synthetic source contract covers buildings, rooms, services, bookings, clinical activity, workforce, finance, and accessibility.

The curated SQLite database keeps source, staging, curated, view, and evidence tables separate. Evidence outputs are exported by stage so lineage can be inspected without re-running unrelated analytics.

Contract checks are run through:

```bash
make validate-config validate-sql
```

No real patient, staff, or estate records are included in this handover.
