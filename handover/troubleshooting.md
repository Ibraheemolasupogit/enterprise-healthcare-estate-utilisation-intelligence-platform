# Troubleshooting

## Missing Database

Run:

```bash
make build-curated-database
make assurance-full
```

## Failed Portfolio Check

Run:

```bash
make portfolio-check
```

Review the reported missing asset, draft-text marker, language-control issue, or status mismatch.

## Simulation Concerns

Simulation concerns are expected synthetic evidence in the current state. Do not remove them to make the pack appear cleaner.

## Dependency Issues

Reinstall the local project with `python3 -m pip install -e ".[dev]"`, then rerun the failing check.
