# Pipeline Runbook

Run the synthetic pipeline in this order:

1. `make generate-sample-data`
2. `make verify-synthetic-data`
3. `make build-curated-database`
4. `make verify-database`
5. `make run-data-quality verify-data-quality`
6. `make calculate-utilisation verify-utilisation`
7. `make run-forecasting verify-forecasting`
8. `make run-scenarios verify-scenarios`
9. `make run-optimisation verify-optimisation`
10. `make run-simulation verify-simulation`
11. `make run-financial-analysis verify-financial-analysis`
12. `make generate-communication-evidence verify-communication-evidence`
13. `make run-assurance verify-assurance`

The grouped equivalent is:

```bash
make assurance-full
```

Simulation resilience failures are evidence and must remain visible.
