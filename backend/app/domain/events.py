"""Source-independent, canonical football event contract.

Adapters translate source payloads into this model. Analytics consumes only
canonical events; provider-only fields belong in ``source.raw_metadata``.
"""

from __future__ import annotations

import re
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_ATTRIBUTE_KEYS = {
    "completed", "on_target", "outcome", "recipient_player_id",
    "previous_team_id", "next_team_id", "intensity", "recovery_type",
}
_SHOT_OUTCOMES = {"goal", "saved", "off_target", "blocked"}


class EventType(str, Enum):
    pass_ = "pass"
    shot = "shot"
    tackle = "tackle"
    interception = "interception"
    possession_change = "possession_change"
    high_regain = "high_regain"
    penalty_box_entry = "penalty_box_entry"
    attacking_third_entry = "attacking_third_entry"
    recovery = "recovery"
    goal = "goal"
    foul = "foul"
    corner = "corner"
    free_kick = "free_kick"
    goal_kick = "goal_kick"
    throw_in = "throw_in"
    substitution = "substitution"
    yellow_card = "yellow_card"
    red_card = "red_card"
    kickoff = "kickoff"
    half_time = "half_time"
    full_time = "full_time"
    pressure_event = "pressure_event"


class Zone(str, Enum):
    defensive_third = "defensive_third"
    middle_third = "middle_third"
    attacking_third = "attacking_third"
    penalty_box = "penalty_box"


class EventSource(BaseModel):
    """Non-authoritative source provenance retained with the event."""

    model_config = ConfigDict(extra="forbid")
    adapter: str = Field(min_length=1, max_length=128)
    source_event_id: str | None = Field(default=None, max_length=128)
    raw_metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("adapter", "source_event_id")
    @classmethod
    def non_blank(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("must not be blank")
        return value


class CanonicalEvent(BaseModel):
    """Validated event used by deterministic MatchPulse components.

    Coordinates use a 0--100 normalized pitch. ``x`` and ``y`` are supplied
    together or omitted together; optional timestamp is independent of clock.
    """

    model_config = ConfigDict(extra="forbid")
    schema_version: str = Field(default="event-v1", pattern=r"^event-v\d+$")
    event_id: str = Field(min_length=1, max_length=128)
    match_id: str = Field(min_length=1, max_length=128)
    minute: int = Field(ge=0, le=150)
    second: int = Field(ge=0, le=59)
    event_type: EventType
    team_id: str = Field(min_length=1, max_length=128)
    player_id: str | None = Field(default=None, min_length=1, max_length=128)
    x: float | None = Field(default=None, ge=0, le=100)
    y: float | None = Field(default=None, ge=0, le=100)
    zone: Zone | None = None
    timestamp: datetime | None = None
    source: EventSource | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)

    @field_validator("event_id", "match_id", "team_id", "player_id")
    @classmethod
    def validate_identifier(cls, value: str | None) -> str | None:
        if value is not None and not _IDENTIFIER.fullmatch(value):
            raise ValueError("must be a stable identifier containing only letters, numbers, '.', '_', ':', or '-'")
        return value

    @field_validator("attributes")
    @classmethod
    def validate_attribute_keys(cls, value: dict[str, Any]) -> dict[str, Any]:
        unknown = set(value).difference(_ATTRIBUTE_KEYS)
        if unknown:
            raise ValueError(f"unsupported canonical attribute(s): {', '.join(sorted(unknown))}")
        if "completed" in value and not isinstance(value["completed"], bool):
            raise ValueError("attributes.completed must be a boolean")
        if "on_target" in value and not isinstance(value["on_target"], bool):
            raise ValueError("attributes.on_target must be a boolean")
        if "intensity" in value and (not isinstance(value["intensity"], (int, float)) or isinstance(value["intensity"], bool) or not 0 <= value["intensity"] <= 100):
            raise ValueError("attributes.intensity must be a number from 0 to 100")
        for key in ("recipient_player_id", "previous_team_id", "next_team_id", "recovery_type"):
            if key in value and (not isinstance(value[key], str) or not value[key].strip()):
                raise ValueError(f"attributes.{key} must be a non-blank string")
        if "outcome" in value and value["outcome"] not in _SHOT_OUTCOMES:
            raise ValueError(f"attributes.outcome must be one of {sorted(_SHOT_OUTCOMES)}")
        return value

    @model_validator(mode="after")
    def validate_event_specific_fields(self) -> "CanonicalEvent":
        if (self.x is None) != (self.y is None):
            raise ValueError("x and y must be supplied together")
        if self.event_type == EventType.goal and self.attributes.get("outcome") not in (None, "goal"):
            raise ValueError("a goal event must have outcome 'goal' when outcome is supplied")
        if self.event_type not in (EventType.shot, EventType.goal) and "on_target" in self.attributes:
            raise ValueError("attributes.on_target is only valid for shot or goal events")
        if self.event_type != EventType.pass_ and any(key in self.attributes for key in ("completed", "recipient_player_id")):
            raise ValueError("pass attributes are only valid for pass events")
        if self.event_type != EventType.possession_change and any(key in self.attributes for key in ("previous_team_id", "next_team_id")):
            raise ValueError("possession transition attributes are only valid for possession_change events")
        if self.event_type != EventType.pressure_event and "intensity" in self.attributes:
            raise ValueError("attributes.intensity is only valid for pressure_event events")
        if self.event_type != EventType.recovery and "recovery_type" in self.attributes:
            raise ValueError("attributes.recovery_type is only valid for recovery events")
        return self

    @property
    def clock_seconds(self) -> int:
        return self.minute * 60 + self.second
