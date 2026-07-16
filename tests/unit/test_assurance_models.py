from estate_intelligence.assurance.models import AssuranceCheck, AssuranceResult


def test_assurance_result_links_to_check() -> None:
    check = AssuranceCheck(
        "ASR-REP-001",
        "repository",
        "Repository",
        "Repository exists.",
        "critical",
        True,
        "method",
        "pass",
        "fix",
        "files",
    )
    result = AssuranceResult(check, "pass", "ok", "abc")

    assert result.check.check_id == "ASR-REP-001"
    assert result.status == "pass"
