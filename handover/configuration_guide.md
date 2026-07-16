# Configuration Guide

Configuration files live under `config`.

Key contracts:

- `settings.yaml` controls foundation runtime settings.
- `synthetic_data.yaml` controls synthetic generation.
- `data_quality.yaml`, `utilisation.yaml`, `forecasting.yaml`, `scenarios.yaml`, `optimisation.yaml`, `simulation.yaml`, and `finance.yaml` configure analytical stages.
- `communication.yaml` controls stakeholder communication evidence.
- `assurance.yaml` controls assurance checks.
- `portfolio.yaml` controls Milestone 14 handover and portfolio validation.

Configuration changes should be followed by:

```bash
make validate-config portfolio-check handover-check final-audit
```
