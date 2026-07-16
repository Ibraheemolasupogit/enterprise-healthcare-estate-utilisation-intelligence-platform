# Repository Structure

This document summarises the final synthetic repository layout for Milestone 14.

- `.github/` contains issue templates, pull request template, CI, and release evidence workflow.
- `config/` contains YAML contracts for settings, synthetic data, analytics, assurance, and portfolio validation.
- `data/sample/` contains committed synthetic source extracts.
- `data/processed/` contains local SQLite evidence databases when generated.
- `database/schema/` and `database/views/` contain SQL contracts.
- `dashboard/` contains the local read-only Streamlit dashboard.
- `docs/` contains methodology, controls, evidence, and final audit documentation.
- `handover/` contains operational runbooks and final handover guidance.
- `outputs/` contains generated synthetic evidence exports.
- `portfolio/` contains presentation-ready synthetic portfolio materials, diagrams, screenshot note, and manifest.
- `src/estate_intelligence/` contains Python packages for each evidence stage.
- `tests/` contains unit, integration, contract, and end-to-end validation.

The structure supports local review and reproducibility. It does not imply real data onboarding, deployment, or governance approval.
