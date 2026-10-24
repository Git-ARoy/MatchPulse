"""Match state tracking models.

MatchState is the authoritative, versioned snapshot of a live match.  Every
time a CanonicalEvent is processed, a new version is emitted with an
auto-incremented state_version.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, Field


class MatchStatus(str, Enum):
    """Current phase of the match."""

    not_started = "not_started"
    first_half = "first_half"
    half_time = "half_time"
    second_half = "second_half"
    full_time = "full_time"


class MatchClock(BaseModel):
    """Simple match-clock representation."""

    minute: int = Field(0, ge=0)
    second: int = Field(0, ge=0, le=59)

    def total_seconds(self) -> int:
        """Return the match clock as elapsed seconds from kick-off."""
        return self.minute * 60 + self.second


class TeamState(BaseModel):
    """Accumulated statistics for a single team within a match."""

    team_id: str
    goals: int = 0
    shots: int = 0
    shots_on_target: int = 0
    passes: int = 0
    passes_completed: int = 0
    tackles: int = 0
    interceptions: int = 0
    fouls: int = 0
    corners: int = 0
    possession_events: int = 0
    high_regains: int = 0
    attacking_third_entries: int = 0
    penalty_box_entries: int = 0
    recoveries: int = 0


class MatchState(BaseModel):
    """Versioned, immutable snapshot of the entire match at a point in time."""

    match_id: str
    state_version: int = 0
    match_clock: MatchClock = Field(default_factory=MatchClock)
    teams: dict[str, TeamState] = Field(default_factory=dict)
    events: list[str] = Field(default_factory=list, description="Ordered list of event IDs processed so far")
    status: MatchStatus = MatchStatus.not_started
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
