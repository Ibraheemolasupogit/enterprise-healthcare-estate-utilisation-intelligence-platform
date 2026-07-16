from estate_intelligence.linking.linkage_quality import summarise_linkage


def test_linkage_quality_summary_counts_methods_and_statuses() -> None:
    summary = summarise_linkage(
        [
            {"match_method": "exact_identifier", "match_status": "matched"},
            {"match_method": "composite_key", "match_status": "manual_review"},
            {"match_method": "normalised_name", "match_status": "unmatched"},
        ]
    )

    assert summary["total"] == 3
    assert summary["exact_matches"] == 1
    assert summary["manual_review_records"] == 1
    assert summary["unmatched_records"] == 1
