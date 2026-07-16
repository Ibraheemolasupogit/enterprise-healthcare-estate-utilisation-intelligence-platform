# Dashboard Operations

Install dependencies:

```bash
python3 -m pip install -e ".[dev]"
```

Validate evidence and imports:

```bash
make dashboard-check
make test-dashboard
```

Launch locally:

```bash
make dashboard
```

The Streamlit server binds to `127.0.0.1` by default. Stop it with `Ctrl+C`.

Required upstream evidence:

- ingestion;
- data quality;
- utilisation;
- forecasting;
- scenarios;
- optimisation;
- simulation;
- financial analysis.

Troubleshooting:

- If the database is missing, run the Milestones 1-10 evidence pipeline.
- If a required evidence table is missing, run the corresponding milestone command.
- If Streamlit is unavailable, install the project with dependencies.

The dashboard is not deployed publicly, does not contain secrets, does not add authentication and does not call external APIs.
# Milestone 13 Dashboard Assurance

Automated assurance validates dashboard imports, local-only Streamlit settings and read-only SQLite access. The dashboard remains a local evidence viewer with no approval controls and no public deployment.

