from estate_intelligence.reporting.challenge import build_required_revision


def test_valid_challenge_revises_analytical_position() -> None:
    revision = build_required_revision(
        "financially attractive candidate",
        (
            "nominally financially positive but not realisable without operational mitigation "
            "and further validation"
        ),
        "CHG-008",
    )

    assert revision.initial_position == "financially attractive candidate"
    assert "not realisable without operational mitigation" in revision.revised_position
    assert revision.status == "complete"
