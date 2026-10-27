"""Core data models and vector mathematics for the Synthetic Match Engine."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class Vector2D:
    """Lightweight 2D vector for pitch kinematics."""

    __slots__ = ("x", "y")

    def __init__(self, x: float = 0.0, y: float = 0.0) -> None:
        self.x = float(x)
        self.y = float(y)

    def __add__(self, other: Vector2D) -> Vector2D:
        return Vector2D(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Vector2D) -> Vector2D:
        return Vector2D(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> Vector2D:
        return Vector2D(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar: float) -> Vector2D:
        return self.__mul__(scalar)

    def magnitude(self) -> float:
        return math.hypot(self.x, self.y)

    def distance_to(self, other: Vector2D) -> float:
        return math.hypot(self.x - other.x, self.y - other.y)

    def normalized(self) -> Vector2D:
        mag = self.magnitude()
        if mag == 0.0:
            return Vector2D(0.0, 0.0)
        return Vector2D(self.x / mag, self.y / mag)

    def clamp(self, min_x: float, max_x: float, min_y: float, max_y: float) -> Vector2D:
        return Vector2D(
            max(min_x, min(max_x, self.x)),
            max(min_y, min(max_y, self.y)),
        )

    def to_dict(self) -> dict[str, float]:
        return {"x": round(self.x, 2), "y": round(self.y, 2)}


class BallState(str, Enum):
    controlled = "controlled"
    loose = "loose"
    ground_pass = "ground_pass"
    lofted_pass = "lofted_pass"
    shot = "shot"
    set_piece = "set_piece"
    out_of_bounds = "out_of_bounds"


class MatchPhase(str, Enum):
    not_started = "not_started"
    first_half = "first_half"
    half_time = "half_time"
    second_half = "second_half"
    full_time = "full_time"


class SetPieceType(str, Enum):
    none = "none"
    kickoff = "kickoff"
    corner = "corner"
    free_kick = "free_kick"
    penalty = "penalty"
    throw_in = "throw_in"
    goal_kick = "goal_kick"


@dataclass
class Player:
    """An individual player agent on the pitch."""

    player_id: str
    name: str
    number: int
    team_id: str
    role: str  # GK, CB, LB, RB, CDM, CM, CAM, LW, RW, ST
    base_x: float  # formation anchor 0..100
    base_y: float  # formation anchor 0..100
    x: float = 0.0
    y: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    speed_rating: float = 75.0
    passing_rating: float = 75.0
    shooting_rating: float = 75.0
    defending_rating: float = 75.0
    aggression_rating: float = 60.0
    yellow_cards: int = 0
    is_sent_off: bool = False
    cooldown_ticks: int = 0  # ticks until next allowed action

    def __post_init__(self) -> None:
        if self.x == 0.0 and self.y == 0.0:
            self.x = self.base_x
            self.y = self.base_y

    @property
    def pos(self) -> Vector2D:
        return Vector2D(self.x, self.y)

    @pos.setter
    def pos(self, v: Vector2D) -> None:
        self.x = v.x
        self.y = v.y

    def to_dict(self) -> dict[str, Any]:
        return {
            "player_id": self.player_id,
            "name": self.name,
            "number": self.number,
            "team_id": self.team_id,
            "role": self.role,
            "x": round(self.x, 2),
            "y": round(self.y, 2),
            "vx": round(self.vx, 2),
            "vy": round(self.vy, 2),
            "yellow_cards": self.yellow_cards,
            "is_sent_off": self.is_sent_off,
        }


@dataclass
class Team:
    """A full team of 11 players and tactical configuration."""

    team_id: str
    name: str
    short_name: str
    primary_color: str
    secondary_color: str
    formation: str
    players: list[Player] = field(default_factory=list)
    attacking_direction: int = 1  # 1 = left to right (towards x=100), -1 = right to left (towards x=0)
    score: int = 0

    def get_player(self, player_id: str) -> Player | None:
        for p in self.players:
            if p.player_id == player_id:
                return p
        return None

    @property
    def active_players(self) -> list[Player]:
        return [p for p in self.players if not p.is_sent_off]


@dataclass
class Ball:
    """The ball entity with physics attributes."""

    x: float = 50.0
    y: float = 50.0
    z: float = 0.0  # height in meters
    vx: float = 0.0
    vy: float = 0.0
    vz: float = 0.0
    state: BallState = BallState.set_piece
    carrier_id: str | None = None
    target_x: float = 50.0
    target_y: float = 50.0
    speed_kph: float = 0.0
    last_touch_team_id: str | None = None
    last_touch_player_id: str | None = None

    @property
    def pos(self) -> Vector2D:
        return Vector2D(self.x, self.y)

    @pos.setter
    def pos(self, v: Vector2D) -> None:
        self.x = v.x
        self.y = v.y

    def to_dict(self) -> dict[str, Any]:
        return {
            "x": round(self.x, 2),
            "y": round(self.y, 2),
            "z": round(self.z, 2),
            "carrier_id": self.carrier_id,
            "state": self.state.value,
            "speed_kph": round(self.speed_kph, 1),
            "last_touch_team_id": self.last_touch_team_id,
            "last_touch_player_id": self.last_touch_player_id,
        }
