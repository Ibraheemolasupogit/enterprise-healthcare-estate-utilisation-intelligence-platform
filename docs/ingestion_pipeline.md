# Ingestion Pipeline

Milestone 3 implements this local workflow:

```text
source discovery
-> checksum verification
-> schema validation
-> source load
-> staging transformation
-> linkage
-> curated acceptance
-> reconciliation
-> evidence export
-> data-quality run
```

The loader reads `data/sample/generation_metadata.json`, verifies SHA-256 checksums for each CSV and checks fixed
headers before loading. Raw source values are inserted into `source_` tables with source file name, source row number,
source checksum and deterministic ingestion run ID.

Staging trims values, converts empty strings to `NULL` where appropriate, records normalised comparison values and marks
rows as `accepted`, `accepted_with_warning` or `rejected`. Milestone 3 keeps documented defects visible rather than
discarding them.

The pipeline rolls back unrecoverable failures within the SQLite transaction. Evidence exports are deterministic CSV and
JSON files under an approved output directory such as `outputs/ingestion`.

Milestone 4 runs after this pipeline. It reads the generated SQLite evidence and curated/staging tables, writes
`evidence_quality_*` tables and exports deterministic quality evidence under `outputs/data_quality`. It does not change
source, staging or curated records.
