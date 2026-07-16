"""Chronological forecast backtesting helpers."""

from __future__ import annotations

from estate_intelligence.forecasting.models import Fold


def generate_folds(
    periods: list[str], initial_training_periods: int, validation_horizon: int, rolling_step: int
) -> list[Fold]:
    """Generate expanding-window chronological folds without future leakage."""

    folds: list[Fold] = []
    train_end = initial_training_periods
    fold_number = 1
    while train_end + validation_horizon <= len(periods):
        validation_start = train_end
        validation_end = train_end + validation_horizon
        folds.append(
            Fold(
                fold_id=f"fold-{fold_number:02d}",
                fold_number=fold_number,
                train_start=0,
                train_end=train_end,
                validation_start=validation_start,
                validation_end=validation_end,
            )
        )
        train_end += rolling_step
        fold_number += 1
    return folds
