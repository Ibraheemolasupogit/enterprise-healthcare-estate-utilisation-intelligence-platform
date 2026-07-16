import pytest

from estate_intelligence.metrics.models import TimeBand
from estate_intelligence.metrics.time_bands import assign_time_band, is_peak_band

BANDS = {
    "early": TimeBand(start="07:00", end="09:00", peak=False),
    "morning_peak": TimeBand(start="09:00", end="12:00", peak=True),
}


def test_time_band_boundaries_are_non_overlapping() -> None:
    assert assign_time_band("07:00", BANDS) == "early"
    assert assign_time_band("08:59", BANDS) == "early"
    assert assign_time_band("09:00", BANDS) == "morning_peak"
    assert is_peak_band("morning_peak", BANDS) is True


def test_time_outside_bands_fails() -> None:
    with pytest.raises(ValueError):
        assign_time_band("12:00", BANDS)
