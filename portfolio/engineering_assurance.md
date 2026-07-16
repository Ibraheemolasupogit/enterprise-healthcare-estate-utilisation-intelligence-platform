# Engineering Assurance

The assurance layer validates synthetic evidence, repository structure, configuration contracts, documentation, security scans, release gates, reproducibility, and dashboard read access.

The latest assurance summary records:

- Assurance run: `ASR-39e9f1b4354fb881`
- Required failures: `0`
- Warnings: `2`
- Release readiness: `engineering_ready_with_conditions`

Warnings and conditional gates are retained as evidence. Milestone 14 does not suppress simulation failures, rewrite financial interpretation, or change governance status.

The final quality path is:

```bash
make final-quality
```

This combines the existing quality and assurance checks with portfolio and handover validation.
