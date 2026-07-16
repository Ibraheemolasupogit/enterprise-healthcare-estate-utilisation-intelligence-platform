from estate_intelligence.scenarios.comparison import score_dimensions


def test_score_dimensions_are_bounded() -> None:
    weights = {
        "capacity": 0.2,
        "service_continuity": 0.15,
        "workforce": 0.15,
        "accessibility": 0.15,
        "recurring_cost": 0.1,
        "implementation_burden": 0.1,
        "data_confidence": 0.1,
        "risk": 0.05,
    }
    rows = score_dimensions(
        capacity_margin=2,
        workforce_ok=True,
        accessibility_ok=False,
        cost_difference=-100,
        burden=0.2,
        confidence="moderate",
        risk_count=1,
        weights=weights,
    )
    raw_values = [row["raw_value"] for row in rows]
    assert all(isinstance(value, int | float) for value in raw_values)
    assert all(0 <= value <= 1 for value in raw_values if isinstance(value, int | float))
