# Technical Decisions

## Local-First Architecture

The repository uses local Python, SQLite, YAML, Streamlit, Make, and pytest so the synthetic platform can be reviewed without external services.

## Deterministic Evidence

Synthetic generation and pipeline stages are deterministic. Evidence exports include run identifiers and checksums where appropriate.

## Persisted Evidence Before Presentation

Dashboard, communication, assurance, and portfolio layers read persisted evidence rather than creating separate analytical conclusions.

## Governance Boundary

The platform separates engineering readiness from governance approval. The final state remains `awaiting_governance_decision`, `not_approved`, and `engineering_ready_with_conditions`.

## Milestone 14 Scope

Milestone 14 adds documentation, handover assets, diagrams, manifest generation, and validation commands. It does not add analytical logic, alter simulation evidence, change financial interpretation, or approve a decision.
