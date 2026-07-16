from estate_intelligence.validation.scoring import score_checks, status_from_score


def test_status_thresholds_are_deterministic() -> None:
    assert status_from_score(100) == "pass"
    assert status_from_score(90) == "pass_with_warnings"
    assert status_from_score(75) == "manual_review_required"
    assert status_from_score(40) == "fail"


def test_score_checks_aggregates_dataset_and_dimension_scores() -> None:
    results = [
        {"dataset": "rooms", "dimension": "completeness", "records_failed": 0},
        {"dataset": "rooms", "dimension": "validity", "records_failed": 1},
        {"dataset": "bookings", "dimension": "validity", "records_failed": 0},
    ]

    dataset_scores, dimension_scores, overall_score, overall_status = score_checks(results)

    assert dataset_scores[1]["dataset"] == "rooms"
    assert dataset_scores[1]["score"] == 50.0
    assert len(dimension_scores) == 3
    assert overall_score == 75.0
    assert overall_status == "manual_review_required"
