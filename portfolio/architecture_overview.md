# Architecture Overview

The platform is organised as a local, deterministic analytics system.

## Layers

- Synthetic source data in `data/sample`
- SQLite analytical store in `data/processed`
- SQL schema and views in `database`
- Python analytics packages in `src/estate_intelligence`
- Streamlit dashboard in `dashboard`
- Evidence exports in `outputs`
- Assurance and release evidence in `outputs/assurance`
- Final synthetic portfolio and handover assets in `portfolio` and `handover`

## Design Choices

The architecture favours reproducibility over external service integration. Each milestone persists evidence with run identifiers and export files so that downstream dashboard, communication, and assurance layers can read the same synthetic facts.

No Milestone 14 code changes analytical conclusions. The portfolio package validates documentation and manifests only.
