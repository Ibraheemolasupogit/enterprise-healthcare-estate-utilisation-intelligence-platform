# Reconciliation Methodology

Milestone 4 extends the Milestone 3 ingestion reconciliation evidence. For each dataset, the quality engine compares
source, staging and curated counts from `evidence_reconciliation_summary`.

## Source To Staging

The source layer stores raw CSV values and source provenance. The staging layer preserves the same record grain while
adding normalised values, record status and warning reasons. Row counts are expected to match for the current synthetic
sample.

## Staging To Curated

Curated tables include accepted and accepted-with-warning records. No records are rejected in the current sample, so
curated row counts are expected to match staging counts. Any future rejected rows must be explainable in evidence.

## Relationship Checks

Referential controls check booking-to-room, clinical-activity-to-room, workforce-to-service, finance-to-building and
accessibility-to-site relationships. Dataset-level reconciliation remains separate from analytics and does not infer
capacity, utilisation or financial benefit.

