from estate_intelligence.simulation.seeds import random_stream, stable_seed


def test_stable_seed_is_deterministic_and_stream_specific() -> None:
    first = stable_seed(90210, "case", "experiment", 1, "arrivals")
    second = stable_seed(90210, "case", "experiment", 1, "arrivals")
    other = stable_seed(90210, "case", "experiment", 1, "duration")

    assert first == second
    assert first != other
    assert random_stream(90210, "x").random() == random_stream(90210, "x").random()
