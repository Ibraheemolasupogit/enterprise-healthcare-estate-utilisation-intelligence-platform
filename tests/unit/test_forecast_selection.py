from estate_intelligence.forecasting.models import ModelResult
from estate_intelligence.forecasting.selection import select_model


def test_selection_prefers_simpler_model_within_tolerance() -> None:
    results = [
        ModelResult("naive", {}, (), (), 1, {"wape": 0.1}, "evaluated"),
        ModelResult("holt_linear", {}, (), (), 1, {"wape": 0.1000001}, "evaluated"),
    ]
    selected = select_model("series", results, "wape", tolerance=0.001)
    assert selected.selected_model_id == "naive"
    assert selected.baseline_beaten_flag is False
