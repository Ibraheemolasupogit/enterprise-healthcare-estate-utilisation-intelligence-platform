"""Repository-relative path helpers."""

from pathlib import Path


def repository_root() -> Path:
    """Resolve the repository root from the installed source tree."""

    return Path(__file__).resolve().parents[3]


def resolve_repo_path(*parts: str | Path) -> Path:
    """Resolve a path under the repository root without creating it."""

    root = repository_root()
    candidate = root.joinpath(*parts).resolve()
    candidate.relative_to(root)
    return candidate
