# Data Dictionary

## Milestone 11 Dashboard

The dashboard introduces no new analytical evidence tables. It reads existing `curated_*` and `evidence_*` tables and derives display-only labels, filters and charts. Dashboard validation resolves lineage from `evidence_*_runs` tables.

All examples are fictional.

## buildings.csv

| Field | Type | Nullable | Description | Constraints | Example | Relationships | Controlled defect |
| --- | --- | --- | --- | --- | --- | --- | --- |
| building_id | string | no | Stable building identifier. | `BLD-###` | `BLD-001` | Referenced by rooms and finance. | no |
| site_id | string | no | Fictional site identifier. | `SITE-##` | `SITE-01` | Referenced by workforce/accessibility. | no |
| building_name | string | no | Fictional building name. | Synthetic only. | `Aurora Diagnostic Centre` | none | no |
| building_type | string | no | Estate category. | controlled category | `acute_diagnostic` | none | no |
| ownership_type | string | no | Owned or leased. | `owned`, `leased` | `leased` | finance lease logic | no |
| lease_start_date | date | yes | Lease start for leased buildings. | before end date | `2021-04-01` | none | no |
| lease_end_date | date | yes | Lease end for leased buildings. | after start date | `2029-03-31` | none | no |
| annual_lease_cost | integer | no | Synthetic annual lease cost. | non-negative | `215000` | finance | yes, via finance reconciliation |
| annual_maintenance_cost | integer | no | Synthetic maintenance cost. | non-negative | `124000` | finance | no |
| annual_energy_cost | integer | no | Synthetic energy cost. | non-negative | `86000` | finance | no |
| floor_area_m2 | integer | no | Floor area. | positive | `6200` | finance cost scaling | no |
| accessibility_rating | string | no | Building accessibility grade. | A-D | `B` | rooms | no |
| condition_rating | string | no | Estate condition grade. | A-D | `C` | finance | no |
| active_flag | boolean | no | Source active marker. | true/false | `true` | none | no |

## rooms.csv

| Field | Type | Nullable | Description | Constraints | Example | Relationships | Controlled defect |
| --- | --- | --- | --- | --- | --- | --- | --- |
| room_id | string | no | Stable room identifier. | `ROOM-####` | `ROOM-0001` | bookings/activity | no |
| building_id | string | no | Parent building. | valid building | `BLD-001` | buildings | no |
| room_name | string | no | Fictional room label. | source label | `Consultation 1` | none | yes, duplicate label |
| room_type | string | no | Room category. | controlled category | `consultation` | services | no |
| capacity | integer | no | Nominal capacity. | 1-80 | `6` | services/bookings | no |
| specialist_equipment | string | yes | Specialist equipment label. | required for diagnostic/specialist canonical records | `ultrasound` | services | yes, blank optional source value |
| accessible_flag | boolean | no | Room accessibility marker. | true/false | `true` | accessibility assessment | no |
| opening_time | time | no | Opening time. | before closing | `08:00` | bookings | no |
| closing_time | time | no | Closing time. | after opening | `18:00` | bookings | no |
| available_hours_per_week | float | no | Source availability. | positive | `50` | future utilisation | no |
| protected_capacity_flag | boolean | no | Protected specialist capacity marker. | true/false | `true` | future decision criteria | no |
| active_flag | boolean | no | Source active marker. | true/false | `true` | none | no |

The `DQ-0001` controlled duplicate-label defect uses the room uniqueness business key
`building_id + normalised room_name`. The canonical duplicate group is `BLD-002|treatment 8`, with members
`ROOM-0002` and `ROOM-0026`.

## services.csv

| Field | Type | Nullable | Description | Constraints | Example | Relationships | Controlled defect |
| --- | --- | --- | --- | --- | --- | --- | --- |
| service_id | string | no | Stable service identifier. | `SVC-###` | `SVC-003` | bookings/activity/workforce | no |
| service_name | string | no | Fictional service name. | synthetic only | `Northstar Imaging Ultrasound` | none | no |
| clinical_specialty | string | no | Specialty or operational category. | synthetic category | `Diagnostics` | none | no |
| minimum_room_type | string | no | Required room type. | controlled category | `diagnostic` | rooms | no |
| specialist_equipment_required | string | yes | Required equipment. | aligned to service | `ultrasound` | rooms | no |
| minimum_capacity | integer | no | Minimum capacity. | positive | `4` | rooms/bookings | no |
| face_to_face_requirement | string | no | Face-to-face need. | low to mandatory | `mandatory` | bookings/activity | no |
| maximum_travel_distance_km | float | no | Synthetic access threshold. | positive | `30` | accessibility | no |
| co_location_requirement | string | no | Co-location need. | synthetic label | `diagnostic_support` | future scenarios | no |
| confidentiality_requirement | string | no | Confidentiality need. | standard/enhanced/strict | `strict` | future options | no |
| remote_eligible_rate | float | no | Remote-eligible share. | 0-1 | `0.35` | activity | no |
| active_flag | boolean | no | Source active marker. | true/false | `true` | none | no |

## bookings.csv

| Field | Type | Nullable | Description | Constraints | Example | Relationships | Controlled defect |
| --- | --- | --- | --- | --- | --- | --- | --- |
| booking_id | string | no | Stable booking identifier. | `BOOK-######` | `BOOK-000001` | none | no |
| room_id | string | no | Booked room. | valid room in clean records | `ROOM-0001` | rooms | no |
| service_id | string | no | Booked service. | valid service | `SVC-001` | services | no |
| booking_date | date | no | Session date. | configured range | `2024-04-02` | activity | no |
| start_time | time | no | Start time. | before end | `08:30` | no overlaps in clean records | no |
| end_time | time | no | End time. | after start | `09:30` | no overlaps in clean records | no |
| booked_duration_minutes | integer | no | Booked duration. | positive | `60` | activity | no |
| booking_status | string | no | Status. | completed/cancelled/planned | `completed` | activity | no |
| cancellation_flag | boolean | no | Cancellation marker. | consistent with status | `false` | activity | no |
| no_show_flag | boolean | no | No-show marker. | zero attendance when true | `false` | activity | no |
| actual_attendance_count | integer | no | Actual attendance. | non-negative | `7` | activity | yes, one anomaly |
| planned_attendance_count | integer | no | Planned attendance. | non-negative | `9` | activity | no |
| session_type | string | no | Session category. | controlled category | `clinic` | activity | no |
| created_date | date | no | Booking creation date. | not after booking | `2024-03-18` | none | no |

## clinical_activity.csv

Fields are monthly aggregate activity records derived from synthetic bookings. Counts are non-negative; completed
contacts equal face-to-face plus remote contacts. Relationships: `service_id` references services and `room_id`
references rooms. No controlled defects are injected in this dataset.

## workforce.csv

Fields describe monthly service/site workforce records. Rates are bounded between 0 and 1. `service_id` references
services and `site_id` references sites. `available_fte` may exceed `planned_fte` for one documented bank-cover defect.

## finance.csv

Fields describe annual synthetic building costs by financial year. All costs are non-negative. `building_id` references
buildings. One owned-building lease-like value is intentionally included for future reconciliation testing; it is not a
savings or investment recommendation.

## accessibility.csv

Fields describe fictional origin-area access to sites. `origin_area` is not a postcode. Public transport score uses a
1-5 synthetic scale, and deprivation decile is 1-10. `site_id` references generated sites. No live mapping service is
used.

## SQLite Curated And Evidence Tables

Milestone 3 loads each CSV into `source_<dataset>`, transforms it into `staging_<dataset>` and writes accepted records
to `curated_<dataset>`. Curated tables retain source file name, source row number, source checksum, ingestion run ID,
record status, warning reason and normalised comparison values.

Evidence tables include ingestion runs, source file checksums, linkage results, unmatched records, duplicate candidates,
reconciliation summary and intentional issue detection. They are deterministic audit evidence for later review.

## SQLite Data Quality Evidence Tables

Milestone 4 adds `evidence_quality_runs`, `evidence_quality_rule_catalogue`,
`evidence_quality_check_results`, `evidence_quality_record_issues`, `evidence_quality_dataset_scores`,
`evidence_quality_dimension_scores`, `evidence_quality_reconciliation_results` and
`evidence_quality_manual_review_queue`.

These tables record quality evidence, scores and manual-review items. They do not alter source, staging or curated
records.

## SQLite Utilisation Evidence Tables

Milestone 5 adds `evidence_utilisation_runs`, `evidence_analytics_population`,
`evidence_analytics_exclusions`, `evidence_room_utilisation`, `evidence_building_utilisation`,
`evidence_site_utilisation`, `evidence_service_utilisation`, `evidence_room_service_utilisation`,
`evidence_time_band_utilisation`, `evidence_monthly_utilisation`, `evidence_underutilisation_flags` and
`evidence_unit_cost_metrics`.

These tables store descriptive utilisation metrics and quality-gating evidence. They do not alter source, staging or
curated records and do not contain recommendations.

## SQLite Forecasting Evidence Tables

Milestone 6 adds `evidence_forecast_runs`, `evidence_forecast_series`,
`evidence_forecast_eligibility`, `evidence_forecast_folds`, `evidence_forecast_model_results`,
`evidence_forecast_model_failures`, `evidence_forecast_selections`, `evidence_forecast_values`,
`evidence_forecast_intervals` and `evidence_forecast_accuracy`.

These tables store deterministic demand forecast evidence, model comparisons, uncertainty intervals and future
forecast values. They do not alter source, staging or curated records and do not contain scenario or estate-change
recommendations.

## SQLite Scenario Evidence Tables

Milestone 7 adds `evidence_scenario_runs`, `evidence_scenario_catalogue`, `evidence_scenario_candidates`,
`evidence_scenario_room_actions`, `evidence_scenario_service_moves`, `evidence_scenario_capacity`,
`evidence_scenario_compatibility`, `evidence_scenario_workforce`, `evidence_scenario_accessibility`,
`evidence_scenario_costs`, `evidence_scenario_constraints`, `evidence_scenario_risks`,
`evidence_scenario_scores` and `evidence_scenario_comparison`.

These tables store deterministic scenario appraisal evidence. They do not alter source, staging or curated records and
do not contain optimisation results, approvals, NPV/payback analysis, or implementation recommendations.

## SQLite Optimisation Evidence Tables

Milestone 8 adds `evidence_optimisation_runs`, `evidence_optimisation_cases`,
`evidence_optimisation_candidates`, `evidence_optimisation_variables`,
`evidence_optimisation_allocations`, `evidence_optimisation_room_status`,
`evidence_optimisation_building_status`, `evidence_optimisation_service_moves`,
`evidence_optimisation_constraints`, `evidence_optimisation_binding_constraints`,
`evidence_optimisation_objective_components`, `evidence_optimisation_solver_results`,
`evidence_optimisation_infeasibility` and `evidence_optimisation_comparison`.

These tables store mathematical allocation evidence only. They do not alter source, staging or curated records and do
not contain approved recommendations, simulation results, NPV or payback analysis.

## SQLite Simulation Evidence Tables

Milestone 9 adds `evidence_simulation_runs`, `evidence_simulation_cases`,
`evidence_simulation_experiments`, `evidence_simulation_replications`,
`evidence_simulation_events`, `evidence_simulation_resource_metrics`,
`evidence_simulation_service_metrics`, `evidence_simulation_queue_metrics`,
`evidence_simulation_workforce_metrics`, `evidence_simulation_resilience_metrics`,
`evidence_simulation_threshold_results`, `evidence_simulation_summary` and
`evidence_simulation_failures`.

These tables store operational simulation evidence only. They do not alter source, staging or curated records and do
not contain clinical validation, final estate recommendations, NPV or payback analysis.
## Financial Evidence

Milestone 10 adds `evidence_financial_runs`, case catalogue, assumptions, recurring cost, transition cost, mitigation cost, cash-flow, payback, NPV, cumulative effect, sensitivity, break-even, risk adjustment, confidence and comparison tables. Amounts are synthetic GBP planning values and are not audited financial records.
