# Assurance Framework

Milestone 13 adds deterministic automated assurance over Milestones 1-12. It orchestrates existing evidence, verifies repository controls, persists `evidence_assurance_*` tables and exports release evidence under `outputs/assurance`.

The framework covers repository, Python, configuration, SQL, synthetic data, ingestion, data quality, utilisation, forecasting, scenarios, optimisation, simulation, finance, dashboard, communication, documentation, security and release gates.

Profiles are explicit:

- `ci_fast` is for bounded pull-request checks.
- `ci_full` is for full local or main-branch validation.
- `canonical` is for deterministic release evidence.

The framework does not deploy, approve an estate decision, publish a package or create new analytics.
