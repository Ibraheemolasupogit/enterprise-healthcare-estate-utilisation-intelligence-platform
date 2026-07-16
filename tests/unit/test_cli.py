import json

import pytest
from typer.testing import CliRunner

from estate_intelligence import __version__
from estate_intelligence.cli import app

runner = CliRunner()


def test_version_command() -> None:
    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0
    assert result.stdout.strip() == __version__


def test_info_command_outputs_public_json() -> None:
    result = runner.invoke(app, ["info"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["package_version"] == __version__
    assert payload["environment"] == "development"
    assert "database_url" not in payload


def test_validate_config_success() -> None:
    result = runner.invoke(app, ["validate-config"])

    assert result.exit_code == 0
    assert "Configuration valid for development" in result.stdout


def test_info_invalid_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ESTATE_INTELLIGENCE_ENVIRONMENT", "invalid")

    result = runner.invoke(app, ["info"])

    assert result.exit_code == 2
    assert "Configuration error" in result.stderr


def test_validate_config_invalid_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ESTATE_INTELLIGENCE_ENVIRONMENT", "invalid")

    result = runner.invoke(app, ["validate-config"])

    assert result.exit_code == 2
    assert "Configuration invalid" in result.stderr
