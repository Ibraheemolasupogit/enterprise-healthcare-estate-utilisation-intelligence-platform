# Installation

The repository is a local Python project using synthetic data and SQLite.

Recommended setup:

```bash
python3 -m pip install -e ".[dev]"
```

If editable extras are unavailable, use:

```bash
python3 -m pip install -e . -r requirements-dev.txt
```

After installation, run:

```bash
make validate-config
make verify-synthetic-data
```

No external data source is required for the synthetic handover pack.
