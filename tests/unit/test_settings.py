from pathlib import Path
from typing import Any, cast

import pytest
from pydantic import ValidationError

from estate_intelligence.settings import Settings
from estate_intelligence.utils.paths import repository_root, resolve_repo_path


def test_settings_defaults_are_safe_for_local_development() -> None:
    settings = Settings()

    assert settings.environment == "development"
    assert settings.log_level == "INFO"
    assert settings.random_seed == 20260714
    assert settings.data_root == Path("data")
    assert "placeholder" in settings.database_url


def test_environment_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ESTATE_INTELLIGENCE_ENVIRONMENT", "staging")
    monkeypatch.setenv("ESTATE_INTELLIGENCE_LOG_LEVEL", "debug")
    monkeypatch.setenv("ESTATE_INTELLIGENCE_RANDOM_SEED", "123")

    settings = Settings()

    assert settings.environment == "staging"
    assert settings.log_level == "DEBUG"
    assert settings.random_seed == 123


def test_invalid_environment_fails_clearly(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ESTATE_INTELLIGENCE_ENVIRONMENT", "sandbox")

    with pytest.raises(ValidationError, match="environment"):
        Settings()


def test_invalid_log_level_fails_clearly(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ESTATE_INTELLIGENCE_LOG_LEVEL", "verbose")

    with pytest.raises(ValidationError, match="log_level"):
        Settings()


def test_path_values_expand_from_strings_and_paths() -> None:
    settings = Settings(
        data_root=cast(Any, "~/estate-data"),
        output_root=Path("~/estate-outputs"),
    )

    assert settings.data_root == Path("~/estate-data").expanduser()
    assert settings.output_root == Path("~/estate-outputs").expanduser()


def test_public_summary_excludes_database_url() -> None:
    settings = Settings(database_url="postgresql://user:secret@example.invalid/db")

    assert "database_url" not in settings.public_summary()
    assert "secret" not in repr(settings.public_summary())


def test_repository_paths_resolve_consistently() -> None:
    root = repository_root()
    resolved = resolve_repo_path("config", "settings.yaml")

    assert root.name == "enterprise-healthcare-estate-utilisation-intelligence-platform"
    assert resolved == root / "config" / "settings.yaml"
