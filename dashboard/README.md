# Milestone 11 Dashboard

This dashboard is a local, read-only Streamlit application over the synthetic Milestones 1-10 SQLite evidence.

Run locally:

```bash
make dashboard
```

Validate without launching a persistent server:

```bash
make dashboard-check
make test-dashboard
```

The app binds to `127.0.0.1`, uses SQLite read-only mode, does not call external APIs and does not approve estate decisions.
