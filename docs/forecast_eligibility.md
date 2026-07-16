# Forecast Eligibility

Every constructed series receives an eligibility result before modelling.

Configured checks include minimum history, non-zero periods, missing-period ratio, variance, recent activity,
intermittency and seasonal history. Outcomes are:

- `eligible`: statistical and baseline models may be evaluated.
- `baseline_only`: intermittent demand restricted to transparent baselines.
- `insufficient_history`: too few historical periods.
- `too_sparse`: too few non-zero periods.
- `constant_series`: no variance; baselines are sufficient.
- `quality_blocked`: missing-period ratio exceeds the configured threshold.
- `inactive_series`: no recent demand.

Ineligible series are evidence, not framework failures.
