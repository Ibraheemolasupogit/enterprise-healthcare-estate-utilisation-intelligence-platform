"""Reusable structured logging setup."""

import logging
from collections.abc import Mapping
from typing import Any


class KeyValueFormatter(logging.Formatter):
    """Format log records with stable key-value fields."""

    def format(self, record: logging.LogRecord) -> str:
        base: Mapping[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        return " ".join(f"{key}={value!r}" for key, value in base.items())


def configure_logging(level: str = "INFO") -> None:
    """Configure application logging without exposing environment contents."""

    handler = logging.StreamHandler()
    handler.setFormatter(KeyValueFormatter())
    logging.basicConfig(level=level.upper(), handlers=[handler], force=True)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger for package modules."""

    return logging.getLogger(name)
