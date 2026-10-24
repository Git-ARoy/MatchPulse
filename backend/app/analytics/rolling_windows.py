"""Amortized O(1) rolling analytics for chronologically ingested events."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field

from app.domain.events import CanonicalEvent, EventType

WINDOW_SECONDS = 300
_WEIGHTS: dict[EventType, int] = {
    EventType.attacking_third_entry: 15, EventType.high_regain: 25,
    EventType.penalty_box_entry: 20, EventType.shot: 25, EventType.goal: 25,
    EventType.pressure_event: 15,
}


@dataclass
class _TeamBuckets:
    current: deque[CanonicalEvent] = field(default_factory=deque)
    previous: deque[CanonicalEvent] = field(default_factory=deque)
    current_score: int = 0
    previous_score: int = 0
    current_shots: int = 0
    previous_shots: int = 0


class RollingWindowCalculator:
    """Two adjacent 300-second windows, with running counters per team.

    Each event moves current → previous → evicted once, giving amortized O(1)
    insertion and O(1) pressure/shot calculations. The service-owned ledger
    remains the source for long-range evidence replay.
    """

    def __init__(self) -> None:
        self._teams: dict[str, _TeamBuckets] = defaultdict(_TeamBuckets)

    def add_event(self, event: CanonicalEvent) -> None:
        bucket = self._teams[event.team_id]
        self._advance(bucket, event.clock_seconds)
        bucket.current.append(event)
        bucket.current_score += _WEIGHTS.get(event.event_type, 0)
        bucket.current_shots += int(event.event_type in (EventType.shot, EventType.goal))

    def pressure_snapshot(self, team_id: str, end_minute: int, end_second: int) -> tuple[float, float | None, float | None]:
        """Return current pressure, delta, and previous pressure in O(1)."""
        now = end_minute * 60 + end_second
        bucket = self._teams[team_id]
        self._advance(bucket, now)
        current = min(100.0, float(bucket.current_score))
        previous = min(100.0, float(bucket.previous_score))
        has_previous_period = now >= WINDOW_SECONDS
        return current, (current - previous if has_previous_period else None), (previous if has_previous_period else None)

    def shot_count(self, team_id: str, end_minute: int, end_second: int) -> int:
        bucket = self._teams[team_id]
        self._advance(bucket, end_minute * 60 + end_second)
        return bucket.current_shots

    @property
    def events(self) -> tuple[CanonicalEvent, ...]:
        return tuple(sorted((event for bucket in self._teams.values() for event in (*bucket.previous, *bucket.current)), key=lambda event: event.clock_seconds))

    def get_all_events_in_window(self, end_minute: int, end_second: int, window_seconds: int = WINDOW_SECONDS) -> list[CanonicalEvent]:
        end = end_minute * 60 + end_second
        return [event for event in self.events if max(0, end - window_seconds) <= event.clock_seconds <= end]

    def get_events_in_window(self, team_id: str, end_minute: int, end_second: int, window_seconds: int = WINDOW_SECONDS) -> list[CanonicalEvent]:
        end = end_minute * 60 + end_second
        bucket = self._teams[team_id]
        self._advance(bucket, end)
        return [event for event in bucket.current if max(0, end - window_seconds) <= event.clock_seconds <= end]

    def get_previous_window_events(self, team_id: str, end_minute: int, end_second: int, window_seconds: int = WINDOW_SECONDS) -> list[CanonicalEvent]:
        end = end_minute * 60 + end_second
        bucket = self._teams[team_id]
        self._advance(bucket, end)
        return [event for event in bucket.previous if max(0, end - 2 * window_seconds) <= event.clock_seconds < max(0, end - window_seconds)]

    def calculate_pressure_index(self, team_id: str, current_window_events: list[CanonicalEvent], previous_window_events: list[CanonicalEvent] | None = None) -> tuple[float, float | None]:
        """Compatibility API for explicitly supplied fixture windows."""
        current = self._score_window(current_window_events)
        previous = self._score_window(previous_window_events) if previous_window_events is not None else None
        return current, (current - previous if previous is not None else None)

    def _advance(self, bucket: _TeamBuckets, now: int) -> None:
        # Current is inclusive: [now - 300, now]. An event exactly on the
        # boundary remains current, matching the public metric contract.
        while bucket.current and bucket.current[0].clock_seconds < now - WINDOW_SECONDS:
            event = bucket.current.popleft()
            bucket.current_score -= _WEIGHTS.get(event.event_type, 0)
            bucket.current_shots -= int(event.event_type in (EventType.shot, EventType.goal))
            bucket.previous.append(event)
            bucket.previous_score += _WEIGHTS.get(event.event_type, 0)
            bucket.previous_shots += int(event.event_type in (EventType.shot, EventType.goal))
        while bucket.previous and bucket.previous[0].clock_seconds < now - 2 * WINDOW_SECONDS:
            event = bucket.previous.popleft()
            bucket.previous_score -= _WEIGHTS.get(event.event_type, 0)
            bucket.previous_shots -= int(event.event_type in (EventType.shot, EventType.goal))

    @staticmethod
    def _score_window(events: list[CanonicalEvent] | None) -> float:
        return min(100.0, float(sum(_WEIGHTS.get(event.event_type, 0) for event in events or [])))
