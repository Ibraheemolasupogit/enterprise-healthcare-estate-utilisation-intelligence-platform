import logging

import pytest

from estate_intelligence.utils.logging import KeyValueFormatter, configure_logging, get_logger


def test_key_value_formatter_outputs_stable_fields() -> None:
    record = logging.LogRecord(
        name="estate_intelligence.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="foundation ready",
        args=(),
        exc_info=None,
    )

    formatted = KeyValueFormatter().format(record)

    assert "level='INFO'" in formatted
    assert "logger='estate_intelligence.test'" in formatted
    assert "message='foundation ready'" in formatted


def test_configure_logging_sets_level_and_uses_formatter(
    capsys: pytest.CaptureFixture[str],
) -> None:
    configure_logging("debug")
    logger = get_logger("estate_intelligence.test")

    logger.debug("debug message")

    captured = capsys.readouterr()
    assert "level='DEBUG'" in captured.err
    assert "debug message" in captured.err
