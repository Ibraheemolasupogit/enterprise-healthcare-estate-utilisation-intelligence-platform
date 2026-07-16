from estate_intelligence.linking.duplicate_detector import detect_duplicates


def test_room_duplicate_detection_is_deterministic() -> None:
    rows = [
        {"room_id": "ROOM-0001", "building_id": "BLD-001", "room_name": "Consultation 1"},
        {"room_id": "ROOM-0002", "building_id": "BLD-001", "room_name": "Consultation 1"},
    ]

    candidates = detect_duplicates("rooms", rows, ingestion_run_id="ING-test")

    assert candidates[0]["duplicate_group_id"].startswith("DUP-")
    assert candidates[0]["duplicate_type"] == "duplicate_room_name_within_building"
