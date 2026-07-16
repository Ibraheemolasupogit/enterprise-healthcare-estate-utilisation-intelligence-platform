from estate_intelligence.linking.common import match_status, similarity
from estate_intelligence.linking.normalisation import normalise_text


def test_normalise_text_collapses_unicode_punctuation_and_space() -> None:
    assert normalise_text("  Aurora—Diagnostic   Centre  ") == "aurora-diagnostic centre"
    assert normalise_text("Cedar Clinic", remove_suffixes=True) == "cedar"


def test_similarity_and_status_bands() -> None:
    assert similarity("Room A", "Room A") == 1.0
    assert match_status(1.0) == "matched"
    assert match_status(0.75) == "manual_review"
    assert match_status(0.5) == "unmatched"
