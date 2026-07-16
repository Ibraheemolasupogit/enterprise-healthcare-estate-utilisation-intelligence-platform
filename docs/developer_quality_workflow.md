# Developer Quality Workflow

Use these local commands for Milestone 13 assurance:

```bash
make validate-repository
make validate-config
make validate-sql
make validate-docs
make scan-secrets
make assurance-fast
make assurance-full
make release-evidence
make verify-release-evidence
make quality
```

`make assurance-full` rebuilds the deterministic Milestones 1-12 evidence chain before running assurance. `make quality` remains the day-to-day developer quality chain.

No command deploys or approves an estate decision.
