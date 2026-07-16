"""Small deterministic event queue used by the simulation engine."""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from typing import Any


@dataclass(order=True)
class ScheduledEvent:
    time: float
    sequence: int
    event_type: str = field(compare=False)
    payload: dict[str, Any] = field(compare=False, default_factory=dict)


class EventQueue:
    """A stable min-heap ordered by event time then insertion sequence."""

    def __init__(self) -> None:
        self._heap: list[ScheduledEvent] = []
        self._sequence = 0

    def schedule(self, time: float, event_type: str, payload: dict[str, Any]) -> None:
        self._sequence += 1
        heapq.heappush(self._heap, ScheduledEvent(time, self._sequence, event_type, payload))

    def pop(self) -> ScheduledEvent:
        return heapq.heappop(self._heap)

    def __bool__(self) -> bool:
        return bool(self._heap)

    def __len__(self) -> int:
        return len(self._heap)
