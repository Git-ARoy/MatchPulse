"""Stateful match tracker.

MatchTracker owns the authoritative MatchState for a single match.  Every
incoming CanonicalEvent is validated, de-duplicated, and applied to produce a
new state version.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.domain.events import CanonicalEvent, EventType, Zone
from app.domain.match_state import MatchClock, MatchState, MatchStatus, TeamState


@dataclass
class ProcessingResult:
    """Outcome of processing a single event."""

    accepted: bool
    duplicate: bool = False
    state_version: int = 0
    message: str = ""


class MatchTracker:
    """Maintains and updates the live match state.

    Thread-safety note: this class is **not** thread-safe.  The caller (API
    layer) is responsible for serialising concurrent writes to the same match.
    """

    def __init__(self, match_id: str) -> None:
        self._match_id = match_id
        self._state = MatchState(
            match_id=match_id,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self._seen_event_ids: set[str] = set()

    @property
    def state(self) -> MatchState:
        return self._state

    def normalize_event(self, event: CanonicalEvent) -> CanonicalEvent:
        """Apply deterministic canonical normalisation after schema validation."""
        if event.zone is None and event.x is not None:
            return event.model_copy(update={"zone": self._infer_zone(event.x)})
        return event

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process_event(self, event: CanonicalEvent) -> ProcessingResult:
        """Apply *event* to the match state.

        Returns a :class:`ProcessingResult` indicating whether the event was
        accepted or rejected (e.g. duplicate).
        """
        # Duplicate guard
        if event.event_id in self._seen_event_ids:
            return ProcessingResult(
                accepted=False,
                duplicate=True,
                state_version=self._state.state_version,
                message=f"Duplicate event {event.event_id}",
            )

        # Match-ID mismatch guard
        if event.match_id != self._match_id:
            return ProcessingResult(
                accepted=False,
                duplicate=False,
                state_version=self._state.state_version,
                message=f"Event match_id '{event.match_id}' does not match tracker match_id '{self._match_id}'",
            )

        # Infer zone from x-coordinate when missing
        event = self.normalize_event(event)

        # Ensure team exists in state
        self._ensure_team(event.team_id)

        # Update match clock
        self._state.match_clock = MatchClock(minute=event.minute, second=event.second)

        # Update match status for lifecycle events
        self._update_status(event.event_type)

        # Dispatch to the appropriate stat updater
        self._apply_event(event)

        # Book-keeping
        self._seen_event_ids.add(event.event_id)
        self._state.events.append(event.event_id)
        self._state.state_version += 1
        self._state.updated_at = datetime.now(UTC)

        return ProcessingResult(
            accepted=True,
            duplicate=False,
            state_version=self._state.state_version,
            message="accepted",
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _infer_zone(x: float) -> Zone:
        """Derive the pitch zone from a normalised x-coordinate.

        x < 33.3  → defensive third
        x < 66.6  → middle third
        x >= 66.6 → attacking third
        """
        if x < 33.3:
            return Zone.defensive_third
        if x < 66.6:
            return Zone.middle_third
        return Zone.attacking_third

    def _ensure_team(self, team_id: str) -> None:
        if team_id not in self._state.teams:
            self._state.teams[team_id] = TeamState(team_id=team_id)

    def _update_status(self, event_type: EventType) -> None:
        if event_type == EventType.kickoff:
            if self._state.status in (MatchStatus.not_started,):
                self._state.status = MatchStatus.first_half
            elif self._state.status == MatchStatus.half_time:
                self._state.status = MatchStatus.second_half
        elif event_type == EventType.half_time:
            self._state.status = MatchStatus.half_time
        elif event_type == EventType.full_time:
            self._state.status = MatchStatus.full_time

    def _apply_event(self, event: CanonicalEvent) -> None:
        """Dispatch the event to the correct stat updater on the team state."""
        ts = self._state.teams[event.team_id]

        handler = _EVENT_HANDLERS.get(event.event_type)
        if handler is not None:
            handler(ts, event)

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    def get_team_state(self, team_id: str) -> TeamState | None:
        return self._state.teams.get(team_id)


# ---------------------------------------------------------------------------
# Event-type handlers
# ---------------------------------------------------------------------------
# Each handler mutates the TeamState in-place.  They are kept outside the class
# to make the mapping table declarative.

def _handle_goal(ts: TeamState, event: CanonicalEvent) -> None:
    ts.goals += 1
    ts.shots += 1
    if event.attributes.get("on_target", True):
        ts.shots_on_target += 1
    _record_shot_speed(ts, event)


def _handle_shot(ts: TeamState, event: CanonicalEvent) -> None:
    ts.shots += 1
    if event.attributes.get("on_target", False):
        ts.shots_on_target += 1
    _record_shot_speed(ts, event)


def _handle_pass(ts: TeamState, event: CanonicalEvent) -> None:
    ts.passes += 1
    if event.attributes.get("completed", False):
        ts.passes_completed += 1
    if (distance := event.attributes.get("distance_m")) is not None:
        ts.pass_distance_total_m += float(distance)
    if (difficulty := event.attributes.get("difficulty_rating")) is not None:
        ts.pass_difficulty_total += float(difficulty)
        ts.pass_difficulty_samples += 1


def _record_shot_speed(ts: TeamState, event: CanonicalEvent) -> None:
    if (speed := event.attributes.get("speed_kph")) is not None:
        ts.shot_speed_total_kph += float(speed)
        ts.shot_speed_samples += 1


def _handle_tackle(ts: TeamState, _event: CanonicalEvent) -> None:
    ts.tackles += 1


def _handle_interception(ts: TeamState, _event: CanonicalEvent) -> None:
    ts.interceptions += 1


def _handle_foul(ts: TeamState, _event: CanonicalEvent) -> None:
    ts.fouls += 1


def _handle_corner(ts: TeamState, _event: CanonicalEvent) -> None:
    ts.corners += 1


def _handle_possession_change(ts: TeamState, _event: CanonicalEvent) -> None:
    ts.possession_events += 1


def _handle_high_regain(ts: TeamState, _event: CanonicalEvent) -> None:
    ts.high_regains += 1


def _handle_attacking_third_entry(ts: TeamState, _event: CanonicalEvent) -> None:
    ts.attacking_third_entries += 1


def _handle_penalty_box_entry(ts: TeamState, _event: CanonicalEvent) -> None:
    ts.penalty_box_entries += 1


def _handle_recovery(ts: TeamState, _event: CanonicalEvent) -> None:
    ts.recoveries += 1


def _handle_pressure_event(ts: TeamState, _event: CanonicalEvent) -> None:
    # Pressure events don't update traditional stats but are tracked for
    # rolling window analytics.
    pass


def _handle_noop(_ts: TeamState, _event: CanonicalEvent) -> None:
    """No stat update for lifecycle / card events beyond what's already tracked."""


_EVENT_HANDLERS: dict[EventType, object] = {
    EventType.goal: _handle_goal,
    EventType.shot: _handle_shot,
    EventType.pass_: _handle_pass,
    EventType.tackle: _handle_tackle,
    EventType.interception: _handle_interception,
    EventType.foul: _handle_foul,
    EventType.corner: _handle_corner,
    EventType.possession_change: _handle_possession_change,
    EventType.high_regain: _handle_high_regain,
    EventType.attacking_third_entry: _handle_attacking_third_entry,
    EventType.penalty_box_entry: _handle_penalty_box_entry,
    EventType.recovery: _handle_recovery,
    EventType.pressure_event: _handle_pressure_event,
    EventType.free_kick: _handle_noop,
    EventType.goal_kick: _handle_noop,
    EventType.throw_in: _handle_noop,
    EventType.substitution: _handle_noop,
    EventType.yellow_card: _handle_noop,
    EventType.red_card: _handle_noop,
    EventType.kickoff: _handle_noop,
    EventType.half_time: _handle_noop,
    EventType.full_time: _handle_noop,
}
