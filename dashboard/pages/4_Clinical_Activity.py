"""Clinical activity dashboard page."""

from __future__ import annotations

from dashboard.components.charts import bar_chart, line_chart
from dashboard.components.filters import select_filter
from dashboard.components.layout import page_header
from dashboard.components.tables import render_table

service = page_header(
    "Clinical Activity", "What clinical activity patterns are visible without patient-level events?"
)
all_rows = service.get_clinical_activity()
service_id = select_filter("Service", [row["service_id"] for row in all_rows], "activity_service")
site_id = select_filter("Site", [row["site_id"] for row in all_rows], "activity_site")
rows = service.get_clinical_activity({"service_id": service_id, "site_id": site_id})

line_chart(rows, "period", "completed_contacts", "Monthly completed-contact trend.")
bar_chart(rows, "service_name", "scheduled_contacts", "Service comparison.")
bar_chart(rows, "service_name", "face_to_face_contacts", "Face-to-face activity mix.")
render_table(rows, "Aggregated clinical activity. Simulated patient-level events are not exposed.")
