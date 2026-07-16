# Dashboard Data Access

The dashboard connects to SQLite using a URI like:

```text
file:/absolute/path/to/estate_intelligence.db?mode=ro
```

The repository also executes:

```sql
PRAGMA query_only = ON
```

Only `SELECT` and `WITH` statements are accepted by the dashboard repository. Mutating statements such as `CREATE`, `INSERT`, `UPDATE`, `DELETE`, `DROP` and `ALTER` are rejected before execution.

Queries use parameter binding for user-facing filters. The dashboard does not accept arbitrary SQL from users.

Run lineage is resolved from `evidence_*_runs` tables at render/check time. IDs are not hard-coded in dashboard code.

The dashboard reads curated and evidence tables only. It does not mutate source, staging, curated or evidence data and does not run upstream analytical pipelines.

