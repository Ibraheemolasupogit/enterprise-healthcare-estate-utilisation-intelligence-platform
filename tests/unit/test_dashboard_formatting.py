from dashboard.components.formatting import currency, percent, status_label


def test_dashboard_formats_status_percent_and_currency() -> None:
    assert status_label("not_realisable_without_mitigation") == "Not realisable without mitigation"
    assert percent(0.1234) == "12.3%"
    assert currency(1234.56) == "GBP 1,235"
