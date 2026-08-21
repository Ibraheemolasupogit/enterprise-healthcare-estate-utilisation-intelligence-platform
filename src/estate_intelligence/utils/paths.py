"""Repository-relative path helpers."""

import os
import tempfile
from pathlib import Path

TEST_MODE_ENV = "ESTATE_INTELLIGENCE_TEST_MODE"


def repository_root() -> Path:
    """Resolve the repository root from the installed source tree."""

    return Path(__file__).resolve().parents[3]


def resolve_repo_path(*parts: str | Path) -> Path:
    """Resolve a path under the repository root without creating it."""

    root = repository_root()
    candidate = root.joinpath(*parts).resolve()
    candidate.relative_to(root)
    return candidate


def approved_test_temp_roots() -> list[Path]:
    """Return test-only temporary roots when explicit test mode is enabled."""

    if os.environ.get(TEST_MODE_ENV) != "1":
        return []
    return [Path(tempfile.gettempdir()).resolve()]
