from dashboard.components.alerts import GLOBAL_NOTICE, NO_RECOMMENDATION


def test_dashboard_alert_copy_keeps_required_warnings_visible() -> None:
    assert "Synthetic demonstration only" in GLOBAL_NOTICE
    assert "No real patient or estate data" in GLOBAL_NOTICE
    assert "No estate decision is approved" in GLOBAL_NOTICE
    assert "Positive nominal NPV does not override" in NO_RECOMMENDATION
