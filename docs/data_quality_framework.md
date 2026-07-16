# Data Quality Framework

Milestone 4 adds a deterministic data-quality and reconciliation layer over the local SQLite ingestion architecture.
It assesses the eight synthetic datasets created in Milestone 2 and loaded in Milestone 3: buildings, rooms, services,
bookings, clinical activity, workforce, finance and accessibility.

The framework is configured by `config/data_quality.yaml`, implemented in `src/estate_intelligence/validation/` and
persisted in `evidence_quality_*` SQLite tables. Runtime exports are written to `outputs/data_quality/` and ignored by
Git.

## Dimensions

- completeness: required and conditionally expected values are present.
- validity: values fit configured domains and basic shapes.
- consistency: fields agree within a record or across closely related records.
- uniqueness: configured identifiers or labels do not create duplicate-review concerns. Room-label uniqueness is
  assessed within a building, not across the whole estate.
- timeliness: source dates are suitable for downstream use against the configured reference date.
- referential_integrity: child records reference accepted parent records.
- reconciliation: source, staging and curated row counts remain explainable.

## Operating Principles

The framework detects, scores and queues issues. It does not silently repair source data, calculate utilisation,
forecast demand, optimise estate allocation, produce recommendations or claim real-world decision approval.

Each run records the ingestion run ID, configuration checksum, rule catalogue checksum, overall score and status. This
makes reruns comparable while preserving the immutable synthetic source files.

Milestone 5 consumes this evidence to exclude manual-review records from utilisation analytics while retaining
accepted-with-warning records according to configuration.
