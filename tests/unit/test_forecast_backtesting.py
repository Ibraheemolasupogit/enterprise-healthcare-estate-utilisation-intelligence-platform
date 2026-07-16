from estate_intelligence.forecasting.backtesting import generate_folds


def test_generate_folds_is_chronological() -> None:
    periods = [f"2025-{month:02d}" for month in range(1, 13)]
    folds = generate_folds(
        periods, initial_training_periods=6, validation_horizon=2, rolling_step=2
    )
    assert [(fold.train_end, fold.validation_start, fold.validation_end) for fold in folds] == [
        (6, 6, 8),
        (8, 8, 10),
        (10, 10, 12),
    ]
