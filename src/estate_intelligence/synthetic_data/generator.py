"""Deterministic synthetic source-data generator for Milestone 2."""

from __future__ import annotations

import json
import random
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Final, Literal, cast

import yaml

from estate_intelligence import __version__
from estate_intelligence.synthetic_data.common import (
    atomic_write_csv,
    atomic_write_json,
    safe_output_dir,
    sha256_file,
    sorted_rows,
)
from estate_intelligence.synthetic_data.metadata import build_metadata
from estate_intelligence.synthetic_data.models import (
    AccessibilityRecord,
    BookingRecord,
    BuildingRecord,
    ClinicalActivityRecord,
    FinanceRecord,
    RoomRecord,
    ServiceRecord,
    WorkforceRecord,
)
from estate_intelligence.utils.paths import repository_root

ORGANISATION_NAME: Final = "Northstar Community Health Partnership"

DATASET_COLUMNS: Final[dict[str, list[str]]] = {
    "buildings": [
        "building_id",
        "site_id",
        "building_name",
        "building_type",
        "ownership_type",
        "lease_start_date",
        "lease_end_date",
        "annual_lease_cost",
        "annual_maintenance_cost",
        "annual_energy_cost",
        "floor_area_m2",
        "accessibility_rating",
        "condition_rating",
        "active_flag",
    ],
    "rooms": [
        "room_id",
        "building_id",
        "room_name",
        "room_type",
        "capacity",
        "specialist_equipment",
        "accessible_flag",
        "opening_time",
        "closing_time",
        "available_hours_per_week",
        "protected_capacity_flag",
        "active_flag",
    ],
    "services": [
        "service_id",
        "service_name",
        "clinical_specialty",
        "minimum_room_type",
        "specialist_equipment_required",
        "minimum_capacity",
        "face_to_face_requirement",
        "maximum_travel_distance_km",
        "co_location_requirement",
        "confidentiality_requirement",
        "remote_eligible_rate",
        "active_flag",
    ],
    "bookings": [
        "booking_id",
        "room_id",
        "service_id",
        "booking_date",
        "start_time",
        "end_time",
        "booked_duration_minutes",
        "booking_status",
        "cancellation_flag",
        "no_show_flag",
        "actual_attendance_count",
        "planned_attendance_count",
        "session_type",
        "created_date",
    ],
    "clinical_activity": [
        "activity_id",
        "service_id",
        "room_id",
        "activity_date",
        "appointment_type",
        "scheduled_contacts",
        "completed_contacts",
        "face_to_face_contacts",
        "remote_contacts",
        "did_not_attend_count",
        "cancelled_contacts",
        "average_contact_duration_minutes",
        "activity_source",
    ],
    "workforce": [
        "workforce_record_id",
        "service_id",
        "site_id",
        "record_date",
        "staff_group",
        "planned_fte",
        "available_fte",
        "absence_rate",
        "remote_working_rate",
        "session_capacity",
        "vacancy_rate",
    ],
    "finance": [
        "finance_record_id",
        "building_id",
        "financial_year",
        "lease_cost",
        "maintenance_cost",
        "utility_cost",
        "security_cost",
        "cleaning_cost",
        "business_rates",
        "planned_capital_cost",
        "exit_cost",
        "relocation_cost",
    ],
    "accessibility": [
        "accessibility_record_id",
        "origin_area",
        "site_id",
        "distance_km",
        "estimated_travel_minutes",
        "public_transport_score",
        "deprivation_decile",
        "accessible_transport_flag",
    ],
}


@dataclass(frozen=True)
class SyntheticDataConfig:
    """Validated generator configuration."""

    master_seed: int = 20260714
    reference_date: date = date(2026, 3, 31)
    start_date: date = date(2024, 4, 1)
    end_date: date = date(2026, 3, 31)
    site_count: int = 4
    building_count: int = 8
    room_count: int = 56
    service_count: int = 12
    booking_count: int = 1440
    workforce_grain: str = "monthly"
    financial_years: tuple[str, ...] = ("2023/24", "2024/25", "2025/26")
    sample_data_scale: str = "small"
    quality_issues_enabled: bool = True
    sample_output_dir: Path = Path("data/sample")
    runtime_output_dir: Path = Path("data/raw")

    @classmethod
    def from_yaml(cls, path: Path | None = None) -> SyntheticDataConfig:
        config_path = path or repository_root() / "config" / "synthetic_data.yaml"
        document = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        if not isinstance(document, dict):
            raise ValueError("synthetic data configuration must be a mapping")
        generation = document["generation"]
        quality = document["quality_issues"]
        paths = document["paths"]
        return cls(
            master_seed=int(generation["master_seed"]),
            reference_date=date.fromisoformat(str(generation["reference_date"])),
            start_date=date.fromisoformat(str(generation["start_date"])),
            end_date=date.fromisoformat(str(generation["end_date"])),
            site_count=int(generation["site_count"]),
            building_count=int(generation["building_count"]),
            room_count=int(generation["room_count"]),
            service_count=int(generation["service_count"]),
            booking_count=int(generation["booking_count"]),
            workforce_grain=str(generation["workforce_grain"]),
            financial_years=tuple(str(year) for year in generation["financial_years"]),
            sample_data_scale=str(generation["sample_data_scale"]),
            quality_issues_enabled=bool(quality["enabled"]),
            sample_output_dir=Path(str(paths["sample_output_dir"])),
            runtime_output_dir=Path(str(paths["runtime_output_dir"])),
        )

    def with_overrides(
        self,
        *,
        seed: int | None = None,
        output_dir: Path | None = None,
        sample: bool = True,
    ) -> SyntheticDataConfig:
        return SyntheticDataConfig(
            master_seed=self.master_seed if seed is None else seed,
            reference_date=self.reference_date,
            start_date=self.start_date,
            end_date=self.end_date,
            site_count=self.site_count,
            building_count=self.building_count,
            room_count=self.room_count,
            service_count=self.service_count,
            booking_count=self.booking_count if sample else self.booking_count * 2,
            workforce_grain=self.workforce_grain,
            financial_years=self.financial_years,
            sample_data_scale=self.sample_data_scale if sample else "runtime",
            quality_issues_enabled=self.quality_issues_enabled,
            sample_output_dir=output_dir or self.sample_output_dir,
            runtime_output_dir=output_dir or self.runtime_output_dir,
        )


def _rng(config: SyntheticDataConfig, dataset: str) -> random.Random:
    seed = config.master_seed + sum((index + 1) * ord(char) for index, char in enumerate(dataset))
    return random.Random(seed)


def generate_all(config: SyntheticDataConfig) -> dict[str, list[dict[str, Any]]]:
    """Generate all canonical datasets as dictionaries ready for serialization."""

    sites = [f"SITE-{index:02d}" for index in range(1, config.site_count + 1)]
    buildings = _generate_buildings(config, sites)
    rooms = _generate_rooms(config, buildings)
    services = _generate_services(config)
    bookings = _generate_bookings(config, rooms, services)
    activity = _generate_activity(config, bookings, services)
    workforce = _generate_workforce(config, sites, services)
    finance = _generate_finance(config, buildings)
    accessibility = _generate_accessibility(config, sites)
    datasets = {
        "buildings": [record.model_dump() for record in buildings],
        "rooms": [record.model_dump() for record in rooms],
        "services": [record.model_dump() for record in services],
        "bookings": [record.model_dump() for record in bookings],
        "clinical_activity": [record.model_dump() for record in activity],
        "workforce": [record.model_dump() for record in workforce],
        "finance": [record.model_dump() for record in finance],
        "accessibility": [record.model_dump() for record in accessibility],
    }
    if config.quality_issues_enabled:
        _inject_quality_issues(datasets)
    return datasets


def data_quality_issues() -> list[dict[str, Any]]:
    """Return stable documentation for intentional synthetic quality issues."""

    return [
        {
            "issue_id": "DQ-0001",
            "dataset": "rooms",
            "record_identifier": "ROOM-0002",
            "field": "room_name",
            "issue_type": "duplicate_label",
            "description": ("Duplicate room name within BLD-002 for future source-quality checks."),
            "duplicate_business_key": "BLD-002|treatment 8",
            "duplicate_group_members": ["ROOM-0002", "ROOM-0026"],
            "expected_rule": "DQ-ROM-UNI-001",
            "expected_action": "manual_review",
            "expected_detection_milestone": 3,
            "severity": "low",
            "intentional": True,
        },
        {
            "issue_id": "DQ-0002",
            "dataset": "rooms",
            "record_identifier": "ROOM-0018",
            "field": "specialist_equipment",
            "issue_type": "missing_optional_source_value",
            "description": (
                "Blank optional equipment value retained from a fictional source extract."
            ),
            "expected_detection_milestone": 3,
            "severity": "low",
            "intentional": True,
        },
        {
            "issue_id": "DQ-0003",
            "dataset": "bookings",
            "record_identifier": "BOOK-000025",
            "field": "actual_attendance_count",
            "issue_type": "attendance_exceeds_planned",
            "description": "One parseable attendance anomaly for future data-quality validation.",
            "expected_detection_milestone": 3,
            "severity": "medium",
            "intentional": True,
        },
        {
            "issue_id": "DQ-0004",
            "dataset": "finance",
            "record_identifier": "FIN-00002",
            "field": "lease_cost",
            "issue_type": "owned_building_lease_reconciliation",
            "description": (
                "Owned building carries a small lease-like charge requiring reconciliation."
            ),
            "expected_detection_milestone": 3,
            "severity": "medium",
            "intentional": True,
        },
        {
            "issue_id": "DQ-0005",
            "dataset": "workforce",
            "record_identifier": "WRK-00007",
            "field": "available_fte",
            "issue_type": "available_above_planned",
            "description": (
                "Temporary bank cover makes available FTE exceed planned FTE in one record."
            ),
            "expected_detection_milestone": 3,
            "severity": "low",
            "intentional": True,
        },
    ]


def write_datasets(
    config: SyntheticDataConfig, output_dir: Path, *, overwrite: bool
) -> dict[str, Any]:
    """Generate and write all datasets plus deterministic metadata."""

    resolved_output = safe_output_dir(output_dir)
    datasets = generate_all(config)
    for dataset_name, rows in datasets.items():
        key = DATASET_COLUMNS[dataset_name][0]
        atomic_write_csv(
            resolved_output / f"{dataset_name}.csv",
            sorted_rows(rows, key),
            DATASET_COLUMNS[dataset_name],
            overwrite=overwrite,
        )
    issues = data_quality_issues() if config.quality_issues_enabled else []
    atomic_write_json(
        resolved_output / "data_quality_issues.json",
        {"issues": issues},
        overwrite=overwrite,
    )
    checksums = {
        f"{dataset}.csv": sha256_file(resolved_output / f"{dataset}.csv")
        for dataset in DATASET_COLUMNS
    }
    checksums["data_quality_issues.json"] = sha256_file(
        resolved_output / "data_quality_issues.json"
    )
    metadata = build_metadata(
        config=config,
        project_version=__version__,
        record_counts={name: len(rows) for name, rows in datasets.items()},
        column_order=DATASET_COLUMNS,
        file_checksums=checksums,
        quality_issue_count=len(issues),
    )
    atomic_write_json(resolved_output / "generation_metadata.json", metadata, overwrite=overwrite)
    return metadata


def verify_output(output_dir: Path) -> dict[str, Any]:
    """Verify generated files, checksums and basic schema presence."""

    resolved = safe_output_dir(output_dir)
    metadata_path = resolved / "generation_metadata.json"
    if not metadata_path.exists():
        raise FileNotFoundError(f"Missing generation metadata: {metadata_path}")
    raw_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if not isinstance(raw_metadata, dict):
        raise ValueError("generation metadata must be a JSON object")
    metadata: dict[str, Any] = raw_metadata
    for dataset_name, columns in DATASET_COLUMNS.items():
        path = resolved / f"{dataset_name}.csv"
        if not path.exists():
            raise FileNotFoundError(f"Missing dataset: {path}")
        with path.open(encoding="utf-8", newline="") as handle:
            header = handle.readline().strip().split(",")
        if header != columns:
            raise ValueError(f"Unexpected columns for {dataset_name}: {header}")
    for filename, checksum in metadata["file_checksums"].items():
        if sha256_file(resolved / filename) != checksum:
            raise ValueError(f"Checksum mismatch for {filename}")
    return metadata


def _generate_buildings(config: SyntheticDataConfig, sites: list[str]) -> list[BuildingRecord]:
    rng = _rng(config, "buildings")
    names = [
        "Aurora Diagnostic Centre",
        "Cedar Community Clinic",
        "Harbour View Offices",
        "Juniper Treatment Wing",
        "Lumen Imaging Hub",
        "Meadowbridge Clinic",
        "Orion Administration House",
        "Willow Specialist Rooms",
    ]
    records: list[BuildingRecord] = []
    for index in range(config.building_count):
        owned = index in {0, 2, 4, 6}
        floor_area = [6200, 1800, 2600, 1100, 4200, 950, 2100, 1400][index]
        condition = ["B", "A", "C", "D", "B", "C", "B", "A"][index]
        lease_cost = 0 if owned else int(floor_area * rng.randint(75, 135))
        building_type = cast(
            Literal[
                "acute_diagnostic",
                "community_clinic",
                "administrative",
                "specialist_treatment",
            ],
            [
                "acute_diagnostic",
                "community_clinic",
                "administrative",
                "specialist_treatment",
            ][index % 4],
        )
        accessibility_rating = cast(
            Literal["A", "B", "C", "D"],
            ["A", "B", "C", "B", "A", "D", "C", "A"][index],
        )
        condition_rating = cast(Literal["A", "B", "C", "D"], condition)
        records.append(
            BuildingRecord(
                building_id=f"BLD-{index + 1:03d}",
                site_id=sites[index % len(sites)],
                building_name=names[index],
                building_type=building_type,
                ownership_type="owned" if owned else "leased",
                lease_start_date=None if owned else date(2022 - index % 3, 4, 1),
                lease_end_date=None if owned else date(2028 + index % 4, 3, 31),
                annual_lease_cost=lease_cost,
                annual_maintenance_cost=int(floor_area * rng.randint(22, 58)),
                annual_energy_cost=int(floor_area * rng.randint(18, 44)),
                floor_area_m2=floor_area,
                accessibility_rating=accessibility_rating,
                condition_rating=condition_rating,
                active_flag=True,
            )
        )
    return records


def _generate_rooms(
    config: SyntheticDataConfig, buildings: list[BuildingRecord]
) -> list[RoomRecord]:
    room_types = ["consultation", "treatment", "diagnostic", "office", "meeting", "specialist"]
    equipment = {
        "consultation": None,
        "treatment": "minor_procedure_couch",
        "diagnostic": "ultrasound",
        "office": None,
        "meeting": None,
        "specialist": "shielded_treatment_bay",
    }
    capacities = {
        "consultation": 4,
        "treatment": 6,
        "diagnostic": 5,
        "office": 8,
        "meeting": 18,
        "specialist": 6,
    }
    records: list[RoomRecord] = []
    for index in range(config.room_count):
        room_type = room_types[index % len(room_types)]
        building = buildings[index % len(buildings)]
        records.append(
            RoomRecord(
                room_id=f"ROOM-{index + 1:04d}",
                building_id=building.building_id,
                room_name=f"{room_type.title()} {index % 9 + 1}",
                room_type=room_type,  # type: ignore[arg-type]
                capacity=capacities[room_type] + (index % 3),
                specialist_equipment=equipment[room_type],
                accessible_flag=building.accessibility_rating in {"A", "B"} or index % 5 != 0,
                opening_time="08:00" if index % 4 else "07:30",
                closing_time="18:00" if index % 4 else "19:00",
                available_hours_per_week=50.0 if index % 4 else 57.5,
                protected_capacity_flag=room_type in {"diagnostic", "specialist"}
                and index % 2 == 0,
                active_flag=True,
            )
        )
    return records


def _generate_services(config: SyntheticDataConfig) -> list[ServiceRecord]:
    definitions = [
        (
            "SVC-001",
            "Northstar Respiratory Assessment",
            "Respiratory",
            "consultation",
            None,
            3,
            "high",
            25.0,
            "none",
            "enhanced",
            0.20,
        ),
        (
            "SVC-002",
            "Northstar Diabetes Review",
            "Endocrinology",
            "consultation",
            None,
            3,
            "medium",
            20.0,
            "none",
            "enhanced",
            0.35,
        ),
        (
            "SVC-003",
            "Northstar Imaging Ultrasound",
            "Diagnostics",
            "diagnostic",
            "ultrasound",
            4,
            "mandatory",
            35.0,
            "diagnostic_support",
            "standard",
            0.0,
        ),
        (
            "SVC-004",
            "Northstar Minor Procedures",
            "Community Surgery",
            "treatment",
            "minor_procedure_couch",
            4,
            "mandatory",
            30.0,
            "sterile_store",
            "strict",
            0.0,
        ),
        (
            "SVC-005",
            "Northstar Therapy Group",
            "Therapies",
            "meeting",
            None,
            12,
            "high",
            18.0,
            "none",
            "standard",
            0.15,
        ),
        (
            "SVC-006",
            "Northstar Child Development",
            "Paediatrics",
            "specialist",
            "shielded_treatment_bay",
            5,
            "mandatory",
            15.0,
            "family_support",
            "strict",
            0.05,
        ),
        (
            "SVC-007",
            "Northstar Frailty Clinic",
            "Older People",
            "consultation",
            None,
            4,
            "high",
            12.0,
            "diagnostic_support",
            "enhanced",
            0.10,
        ),
        (
            "SVC-008",
            "Northstar Administration Hub",
            "Operations",
            "office",
            None,
            6,
            "low",
            40.0,
            "none",
            "standard",
            0.75,
        ),
        (
            "SVC-009",
            "Northstar Staff Training",
            "Workforce",
            "meeting",
            None,
            15,
            "medium",
            50.0,
            "none",
            "standard",
            0.45,
        ),
        (
            "SVC-010",
            "Northstar Cardiac Diagnostics",
            "Cardiology",
            "diagnostic",
            "ultrasound",
            4,
            "mandatory",
            30.0,
            "resus_access",
            "strict",
            0.0,
        ),
        (
            "SVC-011",
            "Northstar Wound Care",
            "Nursing",
            "treatment",
            "minor_procedure_couch",
            3,
            "mandatory",
            18.0,
            "clinical_waste",
            "enhanced",
            0.0,
        ),
        (
            "SVC-012",
            "Northstar Virtual Navigation",
            "Care Coordination",
            "office",
            None,
            4,
            "low",
            60.0,
            "none",
            "enhanced",
            0.85,
        ),
    ]
    return [
        ServiceRecord(
            service_id=row[0],
            service_name=row[1],
            clinical_specialty=row[2],
            minimum_room_type=row[3],  # type: ignore[arg-type]
            specialist_equipment_required=row[4],
            minimum_capacity=row[5],
            face_to_face_requirement=row[6],  # type: ignore[arg-type]
            maximum_travel_distance_km=row[7],
            co_location_requirement=row[8],
            confidentiality_requirement=row[9],  # type: ignore[arg-type]
            remote_eligible_rate=row[10],
            active_flag=True,
        )
        for row in definitions[: config.service_count]
    ]


def _compatible_rooms(rooms: list[RoomRecord], service: ServiceRecord) -> list[RoomRecord]:
    return [
        room
        for room in rooms
        if room.room_type == service.minimum_room_type
        and room.capacity >= service.minimum_capacity
        and (
            service.specialist_equipment_required is None
            or room.specialist_equipment == service.specialist_equipment_required
        )
    ]


def _generate_bookings(
    config: SyntheticDataConfig,
    rooms: list[RoomRecord],
    services: list[ServiceRecord],
) -> list[BookingRecord]:
    rng = _rng(config, "bookings")
    days = [
        config.start_date + timedelta(days=offset)
        for offset in range((config.end_date - config.start_date).days + 1)
        if (config.start_date + timedelta(days=offset)).weekday() < 5
    ]
    start_times = ["08:30", "10:00", "11:30", "13:30", "15:00", "16:30"]
    end_by_start = {
        "08:30": "09:30",
        "10:00": "11:00",
        "11:30": "12:30",
        "13:30": "14:30",
        "15:00": "16:00",
        "16:30": "17:30",
    }
    records: list[BookingRecord] = []
    occupied: set[tuple[str, date, str]] = set()
    index = 0
    while len(records) < config.booking_count:
        service = services[index % len(services)]
        candidate_rooms = _compatible_rooms(rooms, service) or rooms
        room = candidate_rooms[(index + rng.randrange(len(candidate_rooms))) % len(candidate_rooms)]
        booking_date = days[(index * 7 + rng.randrange(len(days))) % len(days)]
        start = start_times[(index + booking_date.month) % len(start_times)]
        slot_key = (room.room_id, booking_date, start)
        index += 1
        if slot_key in occupied:
            continue
        occupied.add(slot_key)
        winter_factor = 1 if booking_date.month in {11, 12, 1, 2} else 0
        planned = max(service.minimum_capacity, 4 + (index % 9) + winter_factor)
        status_roll = rng.random()
        if booking_date > config.reference_date:
            status = "planned"
        elif status_roll < 0.08:
            status = "cancelled"
        else:
            status = "completed"
        no_show = status == "completed" and rng.random() < 0.06
        actual = 0 if status == "cancelled" or no_show else max(1, planned - rng.randint(0, 2))
        records.append(
            BookingRecord(
                booking_id=f"BOOK-{len(records) + 1:06d}",
                room_id=room.room_id,
                service_id=service.service_id,
                booking_date=booking_date,
                start_time=start,
                end_time=end_by_start[start],
                booked_duration_minutes=60,
                booking_status=status,  # type: ignore[arg-type]
                cancellation_flag=status == "cancelled",
                no_show_flag=no_show,
                actual_attendance_count=actual,
                planned_attendance_count=planned,
                session_type=_session_type(service),
                created_date=booking_date - timedelta(days=14 + index % 28),
            )
        )
    return records


def _session_type(
    service: ServiceRecord,
) -> Literal["clinic", "diagnostic", "therapy", "administrative", "virtual_hybrid"]:
    if service.minimum_room_type == "diagnostic":
        return "diagnostic"
    if service.minimum_room_type == "treatment":
        return "therapy"
    if service.minimum_room_type in {"office", "meeting"}:
        return "administrative"
    if service.remote_eligible_rate > 0.5:
        return "virtual_hybrid"
    return "clinic"


def _generate_activity(
    config: SyntheticDataConfig,
    bookings: list[BookingRecord],
    services: list[ServiceRecord],
) -> list[ClinicalActivityRecord]:
    by_group: dict[tuple[str, str, date], list[BookingRecord]] = defaultdict(list)
    for booking in bookings:
        month = date(booking.booking_date.year, booking.booking_date.month, 1)
        by_group[(booking.service_id, booking.room_id, month)].append(booking)
    service_by_id = {service.service_id: service for service in services}
    records: list[ClinicalActivityRecord] = []
    for index, ((service_id, room_id, month), group) in enumerate(
        sorted(by_group.items()), start=1
    ):
        scheduled = sum(item.planned_attendance_count for item in group)
        cancelled = sum(item.planned_attendance_count for item in group if item.cancellation_flag)
        dna = sum(item.planned_attendance_count for item in group if item.no_show_flag)
        completed = sum(item.actual_attendance_count for item in group)
        service = service_by_id[service_id]
        remote = int(completed * service.remote_eligible_rate)
        records.append(
            ClinicalActivityRecord(
                activity_id=f"ACT-{index:05d}",
                service_id=service_id,
                room_id=room_id,
                activity_date=month,
                appointment_type=_appointment_type(service),
                scheduled_contacts=scheduled,
                completed_contacts=completed,
                face_to_face_contacts=completed - remote,
                remote_contacts=remote,
                did_not_attend_count=dna,
                cancelled_contacts=cancelled,
                average_contact_duration_minutes=30
                if service.minimum_room_type == "consultation"
                else 45,
                activity_source="synthetic_booking_summary",
            )
        )
    return records


def _appointment_type(
    service: ServiceRecord,
) -> Literal["first", "follow_up", "procedure", "diagnostic", "administrative"]:
    if service.minimum_room_type == "diagnostic":
        return "diagnostic"
    if service.minimum_room_type == "treatment":
        return "procedure"
    if service.minimum_room_type in {"office", "meeting"}:
        return "administrative"
    return "follow_up"


def _generate_workforce(
    config: SyntheticDataConfig,
    sites: list[str],
    services: list[ServiceRecord],
) -> list[WorkforceRecord]:
    staff_groups = ["medical", "nursing", "allied_health", "administrative", "technical"]
    records: list[WorkforceRecord] = []
    months = _month_starts(config.start_date, config.end_date)
    for month in months:
        for service_index, service in enumerate(services):
            base = 2.0 + (service_index % 4) * 0.8
            absence = (
                0.04 + (0.03 if month.month in {1, 2, 12} else 0.0) + (service_index % 3) * 0.005
            )
            vacancy = 0.03 + (service_index % 5) * 0.01
            planned = round(base, 2)
            records.append(
                WorkforceRecord(
                    workforce_record_id=f"WRK-{len(records) + 1:05d}",
                    service_id=service.service_id,
                    site_id=sites[service_index % len(sites)],
                    record_date=month,
                    staff_group=staff_groups[service_index % len(staff_groups)],  # type: ignore[arg-type]
                    planned_fte=planned,
                    available_fte=round(planned * (1 - absence - vacancy), 2),
                    absence_rate=round(absence, 3),
                    remote_working_rate=round(service.remote_eligible_rate * 0.7, 3),
                    session_capacity=int(planned * 8),
                    vacancy_rate=round(vacancy, 3),
                )
            )
    return records


def _month_starts(start: date, end: date) -> list[date]:
    months: list[date] = []
    current = date(start.year, start.month, 1)
    while current <= end:
        months.append(current)
        current = date(current.year + (current.month // 12), (current.month % 12) + 1, 1)
    return months


def _generate_finance(
    config: SyntheticDataConfig,
    buildings: list[BuildingRecord],
) -> list[FinanceRecord]:
    records: list[FinanceRecord] = []
    for year in config.financial_years:
        for building in buildings:
            condition_factor = {"A": 0.7, "B": 1.0, "C": 1.35, "D": 1.8}[building.condition_rating]
            records.append(
                FinanceRecord(
                    finance_record_id=f"FIN-{len(records) + 1:05d}",
                    building_id=building.building_id,
                    financial_year=year,
                    lease_cost=building.annual_lease_cost,
                    maintenance_cost=int(building.floor_area_m2 * 28 * condition_factor),
                    utility_cost=int(building.floor_area_m2 * 22),
                    security_cost=int(18000 + building.floor_area_m2 * 2),
                    cleaning_cost=int(building.floor_area_m2 * 11),
                    business_rates=int(building.floor_area_m2 * 9),
                    planned_capital_cost=int(50000 * condition_factor)
                    if building.condition_rating in {"C", "D"}
                    else 0,
                    exit_cost=25000
                    if building.ownership_type == "leased" and year == "2025/26"
                    else 0,
                    relocation_cost=15000
                    if building.ownership_type == "leased" and year == "2025/26"
                    else 0,
                )
            )
    return records


def _generate_accessibility(
    config: SyntheticDataConfig, sites: list[str]
) -> list[AccessibilityRecord]:
    origins = [
        "Amber Fields",
        "Birchmoor",
        "Cobalt Vale",
        "Dunlin Park",
        "Elmstead",
        "Fallow Green",
        "Garnet Hill",
        "Hazel Quay",
    ]
    records: list[AccessibilityRecord] = []
    for site_index, site_id in enumerate(sites):
        for origin_index, origin in enumerate(origins):
            distance = round(2.5 + site_index * 4.2 + origin_index * 1.7, 1)
            score = max(1, 5 - int(distance // 8))
            records.append(
                AccessibilityRecord(
                    accessibility_record_id=f"ACC-{len(records) + 1:05d}",
                    origin_area=origin,
                    site_id=site_id,
                    distance_km=distance,
                    estimated_travel_minutes=int(distance * (3.1 if score >= 3 else 4.4) + 8),
                    public_transport_score=score,
                    deprivation_decile=(origin_index + site_index) % 10 + 1,
                    accessible_transport_flag=score >= 3 and origin_index % 4 != 0,
                )
            )
    return records


def _inject_quality_issues(datasets: dict[str, list[dict[str, Any]]]) -> None:
    datasets["rooms"][1]["room_name"] = datasets["rooms"][25]["room_name"]
    datasets["rooms"][17]["specialist_equipment"] = ""
    datasets["bookings"][24]["actual_attendance_count"] = (
        int(datasets["bookings"][24]["planned_attendance_count"]) + 4
    )
    datasets["finance"][1]["lease_cost"] = 1250
    datasets["workforce"][6]["available_fte"] = round(
        float(datasets["workforce"][6]["planned_fte"]) + 0.4, 2
    )
