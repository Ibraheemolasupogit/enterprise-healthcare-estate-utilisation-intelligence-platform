"""Local deterministic repository safety checks."""

from __future__ import annotations

import re
from pathlib import Path

SKIP_PARTS = {".git", ".mypy_cache", ".pytest_cache", ".ruff_cache", "__pycache__"}
TEXT_SUFFIXES = {
    ".cfg",
    ".csv",
    ".env",
    ".example",
    ".ini",
    ".json",
    ".md",
    ".py",
    ".sql",
    ".toml",
    ".txt",
    ".yml",
    ".yaml",
}


def scan_secret_patterns(
    root: Path,
    patterns: list[str],
    allowlist: set[str],
) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    compiled = [re.compile(pattern) for pattern in patterns]
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if not path.is_file() or set(path.parts) & SKIP_PARTS:
            continue
        if path.suffix not in TEXT_SUFFIXES and path.name != ".env.example":
            continue
        if relative in allowlist:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in compiled:
            if pattern.search(text):
                findings.append((relative, pattern.pattern))
    return findings
