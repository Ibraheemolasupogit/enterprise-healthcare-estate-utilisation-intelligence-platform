# Manual Review Process

Manual review is a Milestone 4 queueing mechanism for issues that should remain visible before later analytics.
It does not close issues, approve data use or amend source records.

## Queue Creation

Rules with `failure_action: manual_review` write detected record-level issues to
`evidence_quality_manual_review_queue`. Each row includes the quality run ID, dataset, record identifier, rule ID,
severity, source file reference, recommended review action and status.

## Current Status Model

All generated queue rows start with status `open`. Milestone 4 deliberately excludes workflow assignment, sign-off,
source correction, utilisation calculations and decision approval. Those activities require later governance and
stakeholder processes.

