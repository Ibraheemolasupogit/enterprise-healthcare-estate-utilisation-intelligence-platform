"""Typed runtime settings for the foundation package."""

from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

EnvironmentName = Literal["development", "staging", "production"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Settings(BaseSettings):
    """Application settings loaded from safe defaults and environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="ESTATE_INTELLIGENCE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="forbid",
        frozen=True,
    )

    environment: EnvironmentName = "development"
    project_name: str = "Enterprise Healthcare Estate Utilisation Intelligence Platform"
    log_level: LogLevel = "INFO"
    random_seed: int = Field(default=20260714, ge=0)
    timezone: str = "Europe/London"
    data_root: Path = Path("data")
    output_root: Path = Path("outputs")
    database_url: str = "sqlite:///./local-foundation-placeholder.db"
    config_dir: Path = Path("config")

    @field_validator("log_level", mode="before")
    @classmethod
    def normalise_log_level(cls, value: object) -> object:
        if isinstance(value, str):
            return value.upper()
        return value

    @field_validator("data_root", "output_root", "config_dir", mode="before")
    @classmethod
    def expand_path(cls, value: object) -> object:
        if isinstance(value, str):
            return Path(value).expanduser()
        if isinstance(value, Path):
            return value.expanduser()
        return value

    def public_summary(self) -> dict[str, str | int]:
        """Return non-sensitive values suitable for CLI display and logs."""

        return {
            "environment": self.environment,
            "project_name": self.project_name,
            "log_level": self.log_level,
            "random_seed": self.random_seed,
            "timezone": self.timezone,
            "data_root": str(self.data_root),
            "output_root": str(self.output_root),
            "config_dir": str(self.config_dir),
        }


def load_settings() -> Settings:
    """Load settings from defaults, `.env`, and prefixed environment variables."""

    return Settings()
