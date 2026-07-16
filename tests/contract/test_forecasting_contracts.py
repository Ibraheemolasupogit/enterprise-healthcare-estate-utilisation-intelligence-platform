from pathlib import Path

from estate_intelligence.forecasting.models import ForecastingConfig


def test_forecasting_config_contains_required_targets() -> None:
    config = ForecastingConfig.from_yaml(Path("config/forecasting.yaml"))
    targets = {definition.target for definition in config.series_definitions}
    assert {
        "scheduled_contacts",
        "completed_contacts",
        "face_to_face_contacts",
        "remote_contacts",
        "face_to_face_room_hours",
        "total_room_hour_demand",
        "scheduled_contacts_by_service",
        "completed_contacts_by_service",
        "face_to_face_contacts_by_service",
        "face_to_face_room_hours_by_service",
    }.issubset(targets)
    assert config.forecast_grain == "month"
    assert config.validation_strategy == "expanding_window"
