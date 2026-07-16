from estate_intelligence.financial.payback import payback_year


def test_payback_reached_and_not_reached() -> None:
    assert payback_year([-100.0, 40.0, 70.0]) == "3"
    assert payback_year([-100.0, 10.0], "not_reached") == "not_reached"
