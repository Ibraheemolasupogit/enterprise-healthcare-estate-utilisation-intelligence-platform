# Enterprise Healthcare Estate Utilisation Intelligence Platform

This repository contains a synthetic, local-first healthcare estate utilisation intelligence platform. It demonstrates how estate, room, service, booking, clinical activity, workforce, finance, accessibility, simulation, communication, and assurance evidence can be assembled into a governed decision-support workflow.

The project is complete through Milestone 14: final handover and portfolio pack.

## Current Status

- Evidence boundary: synthetic data only
- Decision status: `awaiting_governance_decision`
- Approval status: `not_approved`
- Engineering release readiness: `engineering_ready_with_conditions`
- Deployment, publication, real data onboarding, and governance approval: outside scope

The platform does not approve estate decisions and does not convert nominal financial impact into realised benefit.

## Main Entry Points

- [Portfolio pack](portfolio/README.md)
- [Handover pack](handover/README.md)
- [Final milestone audit](docs/final_milestone_audit.md)
- [Evidence index](docs/evidence_index.md)
- [Architecture](docs/architecture.md)
- [Dashboard guide](dashboard/README.md)
- [Assurance framework](docs/assurance_framework.md)

## Local Setup

Use Python 3.12.

```bash
python3 -m pip install -e ".[dev]"
```

## Full Local Validation

```bash
python3 -m ruff check .
python3 -m ruff format --check .
python3 -m mypy src dashboard tests
python3 -m pytest
make validate-repository validate-config validate-sql validate-docs scan-secrets
make assurance-full assurance-report release-evidence verify-release-evidence
make dashboard-check portfolio-check handover-check final-audit final-quality
git diff --check
git status --short --branch
```

## Demonstration

Run a read-only dashboard check:

```bash
make dashboard-check
```

Start the local Streamlit dashboard:

```bash
make dashboard
```

Generate or refresh final handover evidence:

```bash
make portfolio-package
```

## Repository Structure

- `config/` contains YAML configuration contracts.
- `data/sample/` contains canonical synthetic sample data.
- `database/` contains SQL schema and views.
- `src/estate_intelligence/` contains the analytics, communication, assurance, and portfolio validation packages.
- `dashboard/` contains the local Streamlit dashboard.
- `outputs/` contains generated synthetic evidence exports.
- `portfolio/` contains the final portfolio pack, diagrams, screenshot note, and manifest.
- `handover/` contains runbooks and operational handover guidance.
- `docs/` contains methodology, audit, architecture, evidence, and decision documentation.
- `tests/` contains unit, integration, contract, and end-to-end checks.

## Synthetic Boundary

No real patient, staff, organisation, estate, finance, or operational records are included. Any future real-world use would require separate information governance, local validation, clinical review, workforce review, finance review, and formal approval.
