"""Resource primitives for room and workforce contention."""

from __future__ import annotations

from dataclasses import dataclass

from estate_intelligence.simulation.models import Arrival, RoomInput


@dataclass
class RoomResource:
    room: RoomInput
    next_free_minute: float = 0.0
    busy_minutes: float = 0.0
    overtime_minutes: float = 0.0
    contention_events: int = 0
    peak_queue_length: int = 0
    capacity_breaches: int = 0

    def assign(self, arrival: Arrival, day_start: float, duration: float) -> tuple[float, float]:
        opening = day_start + self.room.opening_minute
        closing = day_start + self.room.closing_minute
        available_at = max(self.next_free_minute, opening)
        start = max(arrival.arrival_minute, available_at)
        wait = max(0.0, start - arrival.arrival_minute)
        if wait > 0:
            self.contention_events += 1
            self.peak_queue_length = max(self.peak_queue_length, 1)
        finish = start + duration
        if finish > closing:
            self.overtime_minutes += finish - closing
            self.capacity_breaches += 1
        self.busy_minutes += duration
        self.next_free_minute = finish
        return start, finish


@dataclass
class WorkforceResource:
    service_id: str
    capacity_contacts: int
    used_contacts: int = 0
    blocked_contacts: int = 0

    def request(self) -> bool:
        if self.used_contacts >= self.capacity_contacts:
            self.blocked_contacts += 1
            return False
        self.used_contacts += 1
        return True
