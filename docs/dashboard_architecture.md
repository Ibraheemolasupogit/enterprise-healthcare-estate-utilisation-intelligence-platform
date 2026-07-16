# Dashboard Architecture

Milestone 11 adds a local Streamlit dashboard under `dashboard/`. The app is read-only and presents persisted Milestones 1-10 evidence from SQLite.

Structure:

- `dashboard/streamlit_app.py` provides the landing view.
- `dashboard/pages/` contains deterministic multipage views.
- `dashboard/data/repository.py` opens SQLite with `mode=ro` and `PRAGMA query_only = ON`.
- `dashboard/data/services.py` exposes shared page data methods.
- `dashboard/components/` contains alerts, formatting, filters, charts, tables, metrics and provenance helpers.

Pages are thin and do not contain SQL. They call shared services for evidence, use Streamlit-native charts, and show synthetic-data, non-approval, simulation and financial warnings prominently.

Caching, where used in future page refinements, must key by database path and resolved run ID. The current implementation avoids writable connection caching.

Error handling surfaces missing database or missing evidence as dashboard messages and CLI failures. The dashboard does not fabricate fallback values.

