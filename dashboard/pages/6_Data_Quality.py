"""Data quality dashboard page."""

from __future__ import annotations

from dashboard.components.charts import bar_chart
from dashboard.components.layout import page_header
from dashboard.components.tables import render_table

service = page_header(
    "Data Quality", "What data-quality controls, issues and manual reviews remain open?"
)
data = service.get_data_quality_summary()

bar_chart(data["dataset_scores"], "dataset", "score", "Dataset score comparison.")
bar_chart(data["dimension_scores"], "dimension", "score", "Quality dimensions.")
render_table(data["issues"], "Issue counts by severity, action and status.")
render_table(data["manual_review"], "Manual-review queue. Open items are not shown as resolved.")
render_table(data["intentional_detection"], "Intentional-defect detection.")
render_table(data["reconciliation"], "Reconciliation results.")
render_table(data["exclusions"], "Analytical exclusions by dataset.")
