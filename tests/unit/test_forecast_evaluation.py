from estate_intelligence.forecasting.evaluation import bias, mae, rmse, smape, wape


def test_forecast_metrics_handle_defined_and_undefined_cases() -> None:
    actuals = [10.0, 20.0]
    forecasts = [8.0, 23.0]
    assert mae(actuals, forecasts) == 2.5
    rmse_value = rmse(actuals, forecasts)
    assert rmse_value is not None
    assert round(rmse_value, 4) == 2.5495
    assert wape(actuals, forecasts) == 5 / 30
    assert bias(actuals, forecasts) == 0.5
    assert wape([0.0], [1.0]) is None
    assert smape([0.0], [0.0]) == 0.0
