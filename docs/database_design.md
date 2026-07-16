# Database Design

## Dashboard Access

Milestone 11 does not add database tables. The Streamlit dashboard opens `data/processed/estate_intelligence.db` using SQLite URI read-only mode and enables `PRAGMA query_only = ON`. Dashboard filters use parameterised queries and do not execute arbitrary SQL.

Milestone 3 uses SQLite as the required local and reproducible database baseline. The default database path is
`data/processed/estate_intelligence.db`, which is ignored by Git. No cloud database, PostgreSQL service or external
database infrastructure is used.

SQLite does not provide PostgreSQL-style schemas, so layers are represented through explicit table prefixes:

- `source_`: raw CSV values plus source file, row number, checksum and ingestion run provenance.
- `staging_`: trimmed and standardised values, record status, warning reason and normalised comparison fields.
- `curated_`: accepted and accepted-with-warning rows prepared for later milestones, with provenance retained.
- `evidence_`: ingestion runs, source file checksums, linkage results, unmatched records, duplicates, reconciliation and
  intentional-issue detection.
- `evidence_quality_`: data-quality run metadata, rule catalogue rows, check results, record issues, dataset scores,
  dimension scores, reconciliation results and manual-review queue entries.

Dataset-specific source, staging and curated tables are created from the source registry so column order remains aligned
with Milestone 2 contracts. Evidence tables and views are defined in SQL files under `database/schema/` and
`database/views/`.

The pipeline opens SQLite with foreign-key enforcement, a busy timeout and WAL journal mode. Source loading, staging,
curation, linking and evidence creation run inside a transaction. Rebuilds are explicit: existing databases are refused
unless `--rebuild` is passed.

Milestone 4 adds `database/schema/006_data_quality_tables.sql` for deterministic quality evidence. The tables are
audit evidence only: they do not repair source records, calculate utilisation or approve downstream decisions.

Milestone 5 adds `database/schema/007_utilisation_tables.sql` for quality-gated utilisation evidence, analytical
population exclusions, room/building/site/service metrics, time-band/monthly metrics, under-utilisation flags and
descriptive unit-cost metrics.

Milestone 6 adds `database/schema/008_forecasting_tables.sql` for deterministic forecast runs, series, eligibility,
chronological validation folds, model comparisons, model failures, selections, future forecast values, intervals and
accuracy metrics.

Milestone 7 adds `database/schema/009_scenario_tables.sql` for deterministic scenario runs, configured catalogue rows,
candidate rooms, room actions, service-move review rows, capacity evidence, room compatibility, workforce,
accessibility, descriptive cost exposure, constraints, risks, scores and scenario comparison evidence.

Milestone 8 adds `database/schema/010_optimisation_tables.sql` for optimisation runs, cases, candidates, variables,
allocations, room/building status, service moves, constraints, binding constraints, objective components, solver
results, infeasibility diagnostics and case comparison evidence.

Milestone 9 adds `database/schema/011_simulation_tables.sql` for simulation runs, cases, experiments, replications,
sampled events, resource metrics, service metrics, queue metrics, workforce metrics, resilience metrics, thresholds,
summary rows and failure evidence.

Future PostgreSQL portability would require schema-qualified table names, migrations and stricter database-managed
types. That is intentionally not implemented in Milestone 9.
## Financial Schema Extension

`database/schema/012_financial_tables.sql` creates the Milestone 10 financial evidence tables. These tables are append/rebuild analytical evidence tables and preserve upstream run identifiers for ingestion, quality, utilisation, forecasting, scenarios, optimisation and simulation.
# Milestone 13 Assurance Tables

`014_assurance_tables.sql` adds `evidence_assurance_*` tables for assurance runs, check catalogue entries, check results, failures, warnings, reproducibility records, security findings, documentation checks, release gates and manifests. These tables read upstream evidence and do not mutate source, staging or curated records.
