# Data Quality Scoring

Scoring is deterministic and rule-count based. A failed rule is any check result with one or more failed records.
Dataset scores are calculated as passed checks divided by applicable checks. The overall score is the average of the
eight dataset scores.

## Status Bands

| Score | Status |
| --- | --- |
| 95-100 | pass |
| 85-94.99 | pass_with_warnings |
| 70-84.99 | manual_review_required |
| below 70 | fail |

The score is a readiness signal for later milestones. It is not a clinical safety score, estate performance score,
utilisation metric, financial assessment or recommendation.

## Evidence Outputs

Scores are stored in `evidence_quality_dataset_scores` and `evidence_quality_dimension_scores`. The export
`quality_run_summary.json` combines run metadata, scores, issue counts and downstream-readiness text for audit review.

