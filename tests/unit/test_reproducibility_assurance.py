from estate_intelligence.assurance.reproducibility import sha256_text, stable_json


def test_stable_json_is_sorted_and_hashable() -> None:
    left = stable_json({"b": 2, "a": 1})
    right = stable_json({"a": 1, "b": 2})

    assert left == right
    assert sha256_text(left) == sha256_text(right)
