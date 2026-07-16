# Forecast Series

Forecast series use monthly periods from `2024-04` to `2026-03`, followed by the configured future horizon.

| Target | Entity | Source | Unit | Quality treatment |
| --- | --- | --- | --- | --- |
| scheduled_contacts | estate | clinical activity | contacts | included activity only |
| completed_contacts | estate | clinical activity | contacts | included activity only |
| face_to_face_contacts | estate | clinical activity | contacts | included activity only |
| remote_contacts | estate | clinical activity | contacts | included activity only |
| face_to_face_room_hours | estate | clinical activity | room-hours | included activity only |
| total_room_hour_demand | estate | clinical activity | room-hours | included activity only |
| scheduled_contacts_by_service | service | clinical activity | contacts | included activity only |
| completed_contacts_by_service | service | clinical activity | contacts | included activity only |
| face_to_face_contacts_by_service | service | clinical activity | contacts | included activity only |
| face_to_face_room_hours_by_service | service | clinical activity | room-hours | included activity only |
| available_fte_by_service | service | workforce | FTE | included workforce only |
| session_capacity_by_service | service | workforce | sessions | included workforce only |

Complete monthly calendars are created for every series. Observed months retain observation counts. Calendar gaps are
filled with zero and flagged as `calendar_filled_zero`, preserving the difference between an observed zero and a
structurally absent source period.
