from pathlib import Path

from estate_intelligence.assurance.security import scan_secret_patterns


def test_secret_scan_detects_tokens_and_allows_placeholders(tmp_path: Path) -> None:
    (tmp_path / "unsafe.txt").write_text("password=realistic-secret", encoding="utf-8")
    (tmp_path / ".env.example").write_text("PASSWORD=placeholder", encoding="utf-8")

    findings = scan_secret_patterns(tmp_path, [r"(?i)password\s*="], {".env.example"})

    assert findings == [("unsafe.txt", r"(?i)password\s*=")]
