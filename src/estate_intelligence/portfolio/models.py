"""Models for the Milestone 14 portfolio pack."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PortfolioAsset:
    """A file included in the portfolio manifest."""

    path: str
    kind: str
    size_bytes: int
    sha256: str


@dataclass(frozen=True)
class ValidationResult:
    """Result for a portfolio or handover validation pass."""

    ok: bool
    checked: int
    failures: tuple[str, ...]
    warnings: tuple[str, ...] = ()

    def raise_for_failures(self) -> None:
        if self.failures:
            raise ValueError("; ".join(self.failures))


@dataclass(frozen=True)
class PortfolioConfig:
    """Resolved Milestone 14 configuration."""

    path: Path
    required_statuses: dict[str, str]
    portfolio_assets: tuple[str, ...]
    handover_assets: tuple[str, ...]
    diagrams: tuple[str, ...]
    docs: tuple[str, ...]
    forbidden_terms: tuple[str, ...]
    manifest_json: str
    manifest_csv: str
