import csv
from collections import defaultdict
from pathlib import Path

from estate_intelligence.synthetic_data.generator import (
    DATASET_COLUMNS,
    SyntheticDataConfig,
    data_quality_issues,
    generate_all,
    verify_output,
    write_datasets,
)


def test_same_seed_produces_identical_records() -> None:
    config = SyntheticDataConfig()

    assert generate_all(config) == generate_all(config)


def test_different_seed_changes_bookings() -> None:
    default = generate_all(SyntheticDataConfig())
    changed = generate_all(SyntheticDataConfig(master_seed=12345))

    assert default["bookings"] != changed["bookings"]


def test_record_counts_and_field_order() -> None:
    datasets = generate_all(SyntheticDataConfig())

    assert len(datasets["buildings"]) == 8
    assert len(datasets["rooms"]) == 56
    assert len(datasets["services"]) == 12
    assert len(datasets["bookings"]) == 1440
    assert len(datasets["clinical_activity"]) >= 1000
    assert len(datasets["workforce"]) == 288
    assert len(datasets["finance"]) == 24
    assert len(datasets["accessibility"]) == 32
    assert list(datasets["buildings"][0]) == DATASET_COLUMNS["buildings"]


def test_referential_integrity_for_clean_records() -> None:
    datasets = generate_all(SyntheticDataConfig())
    building_ids = {row["building_id"] for row in datasets["buildings"]}
    room_ids = {row["room_id"] for row in datasets["rooms"]}
    service_ids = {row["service_id"] for row in datasets["services"]}
    site_ids = {row["site_id"] for row in datasets["buildings"]}

    assert {row["building_id"] for row in datasets["rooms"]}.issubset(building_ids)
    assert {row["room_id"] for row in datasets["bookings"]}.issubset(room_ids)
    assert {row["service_id"] for row in datasets["bookings"]}.issubset(service_ids)
    assert {row["service_id"] for row in datasets["clinical_activity"]}.issubset(service_ids)
    assert {row["service_id"] for row in datasets["workforce"]}.issubset(service_ids)
    assert {row["site_id"] for row in datasets["workforce"]}.issubset(site_ids)
    assert {row["building_id"] for row in datasets["finance"]}.issubset(building_ids)
    assert {row["site_id"] for row in datasets["accessibility"]}.issubset(site_ids)


def test_operational_ranges_and_documented_defects() -> None:
    datasets = generate_all(SyntheticDataConfig())
    issues = data_quality_issues()

    assert len(issues) == 5
    assert all(issue["intentional"] is True for issue in issues)
    assert all(0 <= float(row["remote_eligible_rate"]) <= 1 for row in datasets["services"])
    assert all(int(row["annual_maintenance_cost"]) >= 0 for row in datasets["buildings"])
    assert all(1 <= int(row["deprivation_decile"]) <= 10 for row in datasets["accessibility"])


def test_duplicate_room_fixture_is_within_one_building() -> None:
    datasets = generate_all(SyntheticDataConfig())
    issues = {issue["issue_id"]: issue for issue in data_quality_issues()}
    rooms = {row["room_id"]: row for row in datasets["rooms"]}
    duplicate_issue = issues["DQ-0001"]
    members = duplicate_issue["duplicate_group_members"]

    assert duplicate_issue["duplicate_business_key"] == "BLD-002|treatment 8"
    assert members == ["ROOM-0002", "ROOM-0026"]
    assert rooms["ROOM-0002"]["building_id"] == rooms["ROOM-0026"]["building_id"] == "BLD-002"
    assert _normalise(rooms["ROOM-0002"]["room_name"]) == _normalise(
        rooms["ROOM-0026"]["room_name"]
    )
    assert rooms["ROOM-0002"]["room_id"] != rooms["ROOM-0026"]["room_id"]


def test_changed_seed_preserves_configured_defect_semantics() -> None:
    datasets = generate_all(SyntheticDataConfig(master_seed=12345))
    duplicate_groups: dict[tuple[str, str], list[str]] = defaultdict(list)
    for row in datasets["rooms"]:
        duplicate_groups[(row["building_id"], _normalise(row["room_name"]))].append(row["room_id"])

    assert sorted(duplicate_groups[("BLD-002", "treatment 8")]) == [
        "ROOM-0002",
        "ROOM-0026",
    ]
    assert datasets["rooms"][17]["specialist_equipment"] == ""
    assert int(datasets["bookings"][24]["actual_attendance_count"]) > int(
        datasets["bookings"][24]["planned_attendance_count"]
    )


def test_write_verify_and_byte_identical_outputs(tmp_path: Path) -> None:
    one = tmp_path / "one"
    two = tmp_path / "two"
    config = SyntheticDataConfig()

    metadata_one = write_datasets(config, one, overwrite=False)
    metadata_two = write_datasets(config, two, overwrite=False)

    assert metadata_one["record_counts"] == metadata_two["record_counts"]
    for name in [*DATASET_COLUMNS, "generation_metadata", "data_quality_issues"]:
        filename = f"{name}.csv" if name in DATASET_COLUMNS else f"{name}.json"
        assert (one / filename).read_bytes() == (two / filename).read_bytes()
    assert verify_output(one)["intentional_quality_issue_count"] == 5


def test_overwrite_refusal(tmp_path: Path) -> None:
    config = SyntheticDataConfig()
    write_datasets(config, tmp_path, overwrite=False)

    try:
        write_datasets(config, tmp_path, overwrite=False)
    except FileExistsError as exc:
        assert "Refusing to overwrite" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected overwrite refusal")


def test_csv_files_parse(tmp_path: Path) -> None:
    write_datasets(SyntheticDataConfig(), tmp_path, overwrite=False)

    for dataset_name, columns in DATASET_COLUMNS.items():
        with (tmp_path / f"{dataset_name}.csv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        assert rows
        assert rows[0].keys() == set(columns)


def _normalise(value: object) -> str:
    return str(value).strip().lower()
