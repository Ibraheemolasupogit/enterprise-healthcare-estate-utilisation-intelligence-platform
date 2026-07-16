import pytest

from estate_intelligence.reporting.service import (
    apply_language_controls,
    validate_language_controls,
)


def test_language_controls_replace_unsafe_phrases() -> None:
    text = apply_language_controls("The optimal solution is financially viable.")

    assert "lowest configured mathematical objective" in text
    assert "nominally financially positive" in text
    assert "not realisable without mitigation" in text


def test_language_controls_reject_forbidden_wording() -> None:
    with pytest.raises(RuntimeError):
        validate_language_controls("The board approved a recommended option.")
