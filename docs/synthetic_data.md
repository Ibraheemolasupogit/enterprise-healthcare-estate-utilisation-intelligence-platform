# Synthetic Data

Milestone 2 creates deterministic synthetic source extracts for the fictional Northstar Community Health Partnership.
The organisation, sites, buildings, services, activity, workforce, finance and accessibility records are invented for
engineering and demonstration purposes only.

The generator is implemented in `src/estate_intelligence/synthetic_data/`. `models.py` defines strict Pydantic record
contracts, `generator.py` creates deterministic records, `common.py` writes stable CSV and JSON files, and `metadata.py`
builds generation metadata.

The default master seed is `20260714`. Dataset-specific random generators derive stable seeds from the master seed and
dataset name. Records are sorted before serialization, columns are fixed, CSV uses UTF-8 with LF endings, and JSON uses
sorted keys. No current timestamp is written to canonical metadata.

The configured date range is `2024-04-01` to `2026-03-31`, with reference date `2026-03-31`. Bookings use weekday
patterns, clinic-session times and winter seasonality. Workforce records are monthly. Finance records cover three
financial years. Accessibility records use fictional origin areas and do not call any mapping or geocoding service.

Dataset relationships are stable:

- rooms reference buildings;
- bookings reference rooms and services;
- clinical activity aggregates booking evidence by service, room and month;
- workforce references services and sites;
- finance references buildings;
- accessibility references sites.

Controlled defects are injected after canonical model generation so model rules remain strict. The defects are small,
parseable and documented in `data/sample/data_quality_issues.json`. They are intended for future data-quality work, not
for Milestone 2 analytics.

The `DQ-0001` duplicate-label fixture is scoped to the Milestone 4 room uniqueness business key:
`building_id + normalised room_name`. In the canonical sample, `ROOM-0002` and `ROOM-0026` are distinct room records in
`BLD-002` with the normalised label `treatment 8`. Same-name rooms in different buildings are not treated as this
defect.

`data/sample/` contains the committed small sample profile. Runtime generation can target `data/raw/` or a temporary
directory. Output paths are restricted to approved project data directories or temporary directories.

Privacy boundary: no real patient data, employee data, organisation data, building data, finance data, postcodes, live
maps or external services are used.

Limitations: the data is realistic enough for later engineering work, but it is not evidence about any real estate
portfolio and must not be used for operational decisions.
