"""Deterministic data-quality scoring."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from typing import Any


def status_from_score(score: float) -> str:
    """Map a score to a configured dataset/run status."""

    if score >= 95:
        return "pass"
    if score >= 85:
        return "pass_with_warnings"
    if score >= 70:
        return "manual_review_required"
    return "fail"


def score_checks(
    results: Iterable[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], float, str]:
    """Score check results by dataset and dimension."""

    grouped: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    dataset_grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for result in results:
        grouped[(str(result["dataset"]), str(result["dimension"]))].append(result)
        dataset_grouped[str(result["dataset"])].append(result)

    dimension_scores: list[dict[str, Any]] = []
    for (dataset, dimension), rows in sorted(grouped.items()):
        failed = sum(1 for row in rows if int(row["records_failed"]) > 0)
        applicable = len(rows)
        score = 100.0 if applicable == 0 else round((applicable - failed) / applicable * 100, 2)
        dimension_scores.append(
            {
                "dataset": dataset,
                "dimension": dimension,
                "score": score,
                "status": status_from_score(score),
                "applicable_checks": applicable,
                "failed_checks": failed,
            }
        )

    dataset_scores: list[dict[str, Any]] = []
    for dataset, rows in sorted(dataset_grouped.items()):
        failed = sum(1 for row in rows if int(row["records_failed"]) > 0)
        total = len(rows)
        score = 100.0 if total == 0 else round((total - failed) / total * 100, 2)
        dataset_scores.append(
            {
                "dataset": dataset,
                "score": score,
                "status": status_from_score(score),
                "passed_checks": total - failed,
                "failed_checks": failed,
            }
        )

    overall_score = (
        100.0
        if not dataset_scores
        else round(sum(float(row["score"]) for row in dataset_scores) / len(dataset_scores), 2)
    )
    return dataset_scores, dimension_scores, overall_score, status_from_score(overall_score)
