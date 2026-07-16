from estate_intelligence.simulation.events import EventQueue


def test_event_queue_orders_by_time_then_sequence() -> None:
    queue = EventQueue()
    queue.schedule(10.0, "arrival", {"id": "b"})
    queue.schedule(5.0, "arrival", {"id": "a"})
    queue.schedule(10.0, "arrival", {"id": "c"})

    assert queue.pop().payload["id"] == "a"
    assert queue.pop().payload["id"] == "b"
    assert queue.pop().payload["id"] == "c"
