from pathlib import Path

PAGE_DIR = Path("dashboard/pages")


def test_dashboard_pages_exist_in_deterministic_order() -> None:
    pages = sorted(path.name for path in PAGE_DIR.glob("*.py"))

    assert pages == [
        "10_Simulation_Resilience.py",
        "11_Financial_Impact.py",
        "12_Evidence_and_Limitations.py",
        "13_Communication_and_Decision_Record.py",
        "1_Executive_Overview.py",
        "2_Estate_Portfolio.py",
        "3_Room_Utilisation.py",
        "4_Clinical_Activity.py",
        "5_Workforce.py",
        "6_Data_Quality.py",
        "7_Forecasting.py",
        "8_Scenario_Comparison.py",
        "9_Optimisation.py",
    ]


def test_dashboard_pages_use_services_not_direct_sqlite() -> None:
    for path in PAGE_DIR.glob("*.py"):
        text = path.read_text()
        assert "DashboardService" not in text
        assert "sqlite3" not in text
        assert "get_" in text
