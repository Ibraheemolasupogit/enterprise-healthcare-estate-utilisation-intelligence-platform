"""Source dataset registry for Milestone 3 ingestion."""

from __future__ import annotations

from dataclasses import dataclass

from estate_intelligence.synthetic_data.generator import DATASET_COLUMNS


@dataclass(frozen=True)
class SourceDataset:
    """Static source dataset contract."""

    name: str
    filename: str
    columns: tuple[str, ...]
    identifier_column: str


SOURCE_DATASETS: tuple[SourceDataset, ...] = tuple(
    SourceDataset(
        name=name,
        filename=f"{name}.csv",
        columns=tuple(columns),
        identifier_column=columns[0],
    )
    for name, columns in DATASET_COLUMNS.items()
)

SOURCE_BY_NAME = {dataset.name: dataset for dataset in SOURCE_DATASETS}
