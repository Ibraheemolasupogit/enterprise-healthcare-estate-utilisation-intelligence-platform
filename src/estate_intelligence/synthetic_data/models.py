"""Pydantic models for deterministic synthetic source datasets."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictRecord(BaseModel):
    """Base model for strict synthetic source records."""

    model_config = ConfigDict(strict=True)


class BuildingRecord(StrictRecord):
    building_id: str = Field(pattern=r"^BLD-\d{3}$")
    site_id: str = Field(pattern=r"^SITE-\d{2}$")
    building_name: str
    building_type: Literal[
        "acute_diagnostic",
        "community_clinic",
        "administrative",
        "specialist_treatment",
    ]
    ownership_type: Literal["owned", "leased"]
    lease_start_date: date | None
    lease_end_date: date | None
    annual_lease_cost: int = Field(ge=0)
    annual_maintenance_cost: int = Field(ge=0)
    annual_energy_cost: int = Field(ge=0)
    floor_area_m2: int = Field(gt=0)
    accessibility_rating: Literal["A", "B", "C", "D"]
    condition_rating: Literal["A", "B", "C", "D"]
    active_flag: bool

    @model_validator(mode="after")
    def validate_lease_dates(self) -> BuildingRecord:
        if self.ownership_type == "leased":
            if self.lease_start_date is None or self.lease_end_date is None:
                raise ValueError("leased buildings require lease dates")
            if self.lease_start_date >= self.lease_end_date:
                raise ValueError("lease_start_date must be before lease_end_date")
        if self.ownership_type == "owned" and (
            self.lease_start_date is not None
            or self.lease_end_date is not None
            or self.annual_lease_cost != 0
        ):
            raise ValueError("owned buildings must not carry lease dates or lease cost")
        return self


class RoomRecord(StrictRecord):
    room_id: str = Field(pattern=r"^ROOM-\d{4}$")
    building_id: str = Field(pattern=r"^BLD-\d{3}$")
    room_name: str
    room_type: Literal[
        "consultation",
        "treatment",
        "diagnostic",
        "office",
        "meeting",
        "specialist",
    ]
    capacity: int = Field(ge=1, le=80)
    specialist_equipment: str | None
    accessible_flag: bool
    opening_time: str = Field(pattern=r"^\d{2}:\d{2}$")
    closing_time: str = Field(pattern=r"^\d{2}:\d{2}$")
    available_hours_per_week: float = Field(gt=0, le=84)
    protected_capacity_flag: bool
    active_flag: bool

    @model_validator(mode="after")
    def validate_opening_pattern(self) -> RoomRecord:
        if self.opening_time >= self.closing_time:
            raise ValueError("opening_time must be before closing_time")
        if self.room_type in {"diagnostic", "specialist"} and not self.specialist_equipment:
            raise ValueError("diagnostic and specialist rooms require specialist_equipment")
        return self


class ServiceRecord(StrictRecord):
    service_id: str = Field(pattern=r"^SVC-\d{3}$")
    service_name: str
    clinical_specialty: str
    minimum_room_type: Literal[
        "consultation",
        "treatment",
        "diagnostic",
        "office",
        "meeting",
        "specialist",
    ]
    specialist_equipment_required: str | None
    minimum_capacity: int = Field(ge=1, le=80)
    face_to_face_requirement: Literal["low", "medium", "high", "mandatory"]
    maximum_travel_distance_km: float = Field(gt=0, le=80)
    co_location_requirement: str
    confidentiality_requirement: Literal["standard", "enhanced", "strict"]
    remote_eligible_rate: float = Field(ge=0, le=1)
    active_flag: bool


class BookingRecord(StrictRecord):
    booking_id: str = Field(pattern=r"^BOOK-\d{6}$")
    room_id: str
    service_id: str = Field(pattern=r"^SVC-\d{3}$")
    booking_date: date
    start_time: str = Field(pattern=r"^\d{2}:\d{2}$")
    end_time: str = Field(pattern=r"^\d{2}:\d{2}$")
    booked_duration_minutes: int = Field(gt=0, le=480)
    booking_status: Literal["completed", "cancelled", "planned"]
    cancellation_flag: bool
    no_show_flag: bool
    actual_attendance_count: int = Field(ge=0)
    planned_attendance_count: int = Field(ge=0)
    session_type: Literal[
        "clinic",
        "diagnostic",
        "therapy",
        "administrative",
        "virtual_hybrid",
    ]
    created_date: date

    @model_validator(mode="after")
    def validate_status_counts(self) -> BookingRecord:
        if self.start_time >= self.end_time:
            raise ValueError("start_time must be before end_time")
        if self.created_date > self.booking_date:
            raise ValueError("created_date must not be after booking_date")
        if self.booking_status == "cancelled" and not self.cancellation_flag:
            raise ValueError("cancelled bookings must set cancellation_flag")
        if self.booking_status == "cancelled" and self.actual_attendance_count != 0:
            raise ValueError("cancelled bookings must not have attendance")
        if self.no_show_flag and self.actual_attendance_count != 0:
            raise ValueError("no-show bookings must not have attendance")
        if self.actual_attendance_count > self.planned_attendance_count:
            raise ValueError("actual attendance must not exceed planned attendance")
        return self


class ClinicalActivityRecord(StrictRecord):
    activity_id: str = Field(pattern=r"^ACT-\d{5}$")
    service_id: str = Field(pattern=r"^SVC-\d{3}$")
    room_id: str
    activity_date: date
    appointment_type: Literal["first", "follow_up", "procedure", "diagnostic", "administrative"]
    scheduled_contacts: int = Field(ge=0)
    completed_contacts: int = Field(ge=0)
    face_to_face_contacts: int = Field(ge=0)
    remote_contacts: int = Field(ge=0)
    did_not_attend_count: int = Field(ge=0)
    cancelled_contacts: int = Field(ge=0)
    average_contact_duration_minutes: int = Field(gt=0, le=240)
    activity_source: Literal["synthetic_booking_summary", "synthetic_service_return"]

    @model_validator(mode="after")
    def validate_contact_components(self) -> ClinicalActivityRecord:
        if self.completed_contacts != self.face_to_face_contacts + self.remote_contacts:
            raise ValueError("completed contacts must equal face-to-face plus remote contacts")
        if self.scheduled_contacts < (
            self.completed_contacts + self.did_not_attend_count + self.cancelled_contacts
        ):
            raise ValueError("scheduled contacts must cover completed, DNA and cancelled contacts")
        return self


class WorkforceRecord(StrictRecord):
    workforce_record_id: str = Field(pattern=r"^WRK-\d{5}$")
    service_id: str = Field(pattern=r"^SVC-\d{3}$")
    site_id: str
    record_date: date
    staff_group: Literal["medical", "nursing", "allied_health", "administrative", "technical"]
    planned_fte: float = Field(ge=0)
    available_fte: float = Field(ge=0)
    absence_rate: float = Field(ge=0, le=1)
    remote_working_rate: float = Field(ge=0, le=1)
    session_capacity: int = Field(ge=0)
    vacancy_rate: float = Field(ge=0, le=1)


class FinanceRecord(StrictRecord):
    finance_record_id: str = Field(pattern=r"^FIN-\d{5}$")
    building_id: str = Field(pattern=r"^BLD-\d{3}$")
    financial_year: str = Field(pattern=r"^\d{4}/\d{2}$")
    lease_cost: int = Field(ge=0)
    maintenance_cost: int = Field(ge=0)
    utility_cost: int = Field(ge=0)
    security_cost: int = Field(ge=0)
    cleaning_cost: int = Field(ge=0)
    business_rates: int = Field(ge=0)
    planned_capital_cost: int = Field(ge=0)
    exit_cost: int = Field(ge=0)
    relocation_cost: int = Field(ge=0)


class AccessibilityRecord(StrictRecord):
    accessibility_record_id: str = Field(pattern=r"^ACC-\d{5}$")
    origin_area: str
    site_id: str
    distance_km: float = Field(ge=0, le=80)
    estimated_travel_minutes: int = Field(ge=0, le=180)
    public_transport_score: int = Field(ge=1, le=5)
    deprivation_decile: int = Field(ge=1, le=10)
    accessible_transport_flag: bool

    @field_validator("origin_area")
    @classmethod
    def reject_real_postcode_like_values(cls, value: str) -> str:
        if any(char.isdigit() for char in value):
            raise ValueError("origin_area must be a fictional area label, not a postcode")
        return value
