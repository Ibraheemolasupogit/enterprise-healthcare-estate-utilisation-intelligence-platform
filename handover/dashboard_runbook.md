# Dashboard Runbook

Validate dashboard read access first:

```bash
make dashboard-check
```

Start the synthetic dashboard:

```bash
make dashboard
```

Inspect executive, estate, room, forecasting, scenario, optimisation, simulation, finance, communication, and limitations pages. The dashboard should read from persisted evidence and should not write analytical data.

If screenshots are required, capture them only from this local Streamlit session and keep warnings visible.
