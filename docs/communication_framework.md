# Communication Framework

Milestone 12 translates synthetic Milestones 1-11 evidence into deterministic audience-specific products. It does not create real communications, approvals, recommendations or stakeholder quotations.

Milestone 13 assurance verifies the communication decision status remains `awaiting_governance_decision` and approval status remains `not_approved`.

The shared reporting service resolves current run lineage from SQLite, loads persisted analytical summaries, constructs options, applies language controls, records objections and revisions, writes `evidence_communication_*` tables and exports Markdown, CSV and JSON products under `outputs/communication/`.

Audiences:

- executive leaders;
- clinical and operational leaders;
- finance stakeholders;
- estates and facilities stakeholders;
- technical and analytical reviewers.

The communication boundary is:

```text
Analytical feasibility is not operational resilience is not financial realisability is not governance approval.
```

All evidence remains synthetic, non-audited and non-approving.
