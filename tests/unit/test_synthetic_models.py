from datetime import date

import pytest
from pydantic import ValidationError

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


def test_building_model_enforces_lease_rules() -> None:
    with pytest.raises(ValidationError, match="owned buildings"):
        BuildingRecord(
            building_id="BLD-001",
            site_id="SITE-01",
            building_name="Fictional House",
            building_type="administrative",
            ownership_type="owned",
            lease_start_date=None,
            lease_end_date=None,
            annual_lease_cost=10,
            annual_maintenance_cost=1,
            annual_energy_cost=1,
            floor_area_m2=100,
            accessibility_rating="A",
            condition_rating="B",
            active_flag=True,
        )


def test_room_model_enforces_opening_order_and_specialist_equipment() -> None:
    with pytest.raises(ValidationError, match="opening_time"):
        RoomRecord(
            room_id="ROOM-0001",
            building_id="BLD-001",
            room_name="Diagnostic 1",
            room_type="diagnostic",
            capacity=5,
            specialist_equipment="ultrasound",
            accessible_flag=True,
            opening_time="18:00",
            closing_time="08:00",
            available_hours_per_week=40.0,
            protected_capacity_flag=True,
            active_flag=True,
        )


def test_service_model_bounds_remote_rate() -> None:
    with pytest.raises(ValidationError):
        ServiceRecord(
            service_id="SVC-001",
            service_name="Northstar Fictional Clinic",
            clinical_specialty="Fictional",
            minimum_room_type="consultation",
            specialist_equipment_required=None,
            minimum_capacity=3,
            face_to_face_requirement="medium",
            maximum_travel_distance_km=20.0,
            co_location_requirement="none",
            confidentiality_requirement="standard",
            remote_eligible_rate=1.5,
            active_flag=True,
        )


def test_booking_model_enforces_attendance_consistency() -> None:
    with pytest.raises(ValidationError, match="actual attendance"):
        BookingRecord(
            booking_id="BOOK-000001",
            room_id="ROOM-0001",
            service_id="SVC-001",
            booking_date=date(2024, 4, 2),
            start_time="09:00",
            end_time="10:00",
            booked_duration_minutes=60,
            booking_status="completed",
            cancellation_flag=False,
            no_show_flag=False,
            actual_attendance_count=6,
            planned_attendance_count=5,
            session_type="clinic",
            created_date=date(2024, 3, 20),
        )


def test_activity_model_reconciles_components() -> None:
    with pytest.raises(ValidationError, match="completed contacts"):
        ClinicalActivityRecord(
            activity_id="ACT-00001",
            service_id="SVC-001",
            room_id="ROOM-0001",
            activity_date=date(2024, 4, 1),
            appointment_type="follow_up",
            scheduled_contacts=10,
            completed_contacts=8,
            face_to_face_contacts=5,
            remote_contacts=1,
            did_not_attend_count=1,
            cancelled_contacts=1,
            average_contact_duration_minutes=30,
            activity_source="synthetic_booking_summary",
        )


def test_rate_and_cost_models_validate_ranges() -> None:
    with pytest.raises(ValidationError):
        WorkforceRecord(
            workforce_record_id="WRK-00001",
            service_id="SVC-001",
            site_id="SITE-01",
            record_date=date(2024, 4, 1),
            staff_group="medical",
            planned_fte=2.0,
            available_fte=1.8,
            absence_rate=1.2,
            remote_working_rate=0.1,
            session_capacity=12,
            vacancy_rate=0.1,
        )
    with pytest.raises(ValidationError):
        FinanceRecord(
            finance_record_id="FIN-00001",
            building_id="BLD-001",
            financial_year="2024/25",
            lease_cost=-1,
            maintenance_cost=1,
            utility_cost=1,
            security_cost=1,
            cleaning_cost=1,
            business_rates=1,
            planned_capital_cost=0,
            exit_cost=0,
            relocation_cost=0,
        )
    with pytest.raises(ValidationError, match="postcode"):
        AccessibilityRecord(
            accessibility_record_id="ACC-00001",
            origin_area="AB1",
            site_id="SITE-01",
            distance_km=5.0,
            estimated_travel_minutes=20,
            public_transport_score=4,
            deprivation_decile=5,
            accessible_transport_flag=True,
        )
