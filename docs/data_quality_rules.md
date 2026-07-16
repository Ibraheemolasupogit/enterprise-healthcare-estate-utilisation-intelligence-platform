# Data Quality Rules

The Milestone 4 rule catalogue contains one rule for every dataset and quality dimension, for 56 rules in total.
Rules are created from typed Pydantic models in `estate_intelligence.validation.models` and assembled by
`estate_intelligence.validation.rules`.

## Catalogue Shape

- datasets: 8
- dimensions: 7
- total rules: 56
- default action: accept
- warning action: accept_with_warning
- material issue action: manual_review

## Intentional Defect Controls

| Intentional defect | Dataset | Rule | Dimension | Failure action |
| --- | --- | --- | --- | --- |
| DQ-0001 | rooms | DQ-ROM-UNI-001 | uniqueness | manual_review |
| DQ-0002 | rooms | DQ-ROM-CMP-001 | completeness | accept_with_warning |
| DQ-0003 | bookings | DQ-BKG-CON-001 | consistency | manual_review |
| DQ-0004 | finance | DQ-FIN-CON-001 | consistency | manual_review |
| DQ-0005 | workforce | DQ-WRK-CON-001 | consistency | accept_with_warning |

`DQ-ROM-UNI-001` evaluates duplicate room labels within a building, using `building_id + normalised room_name`.
The canonical `DQ-0001` duplicate group is `BLD-002|treatment 8`, with members `ROOM-0002` and `ROOM-0026`.
Repeated room names in different buildings are not failures for this rule.

Passing rules remain recorded in `evidence_quality_check_results` so the evidence base shows both failures and
controls that found no issue.
