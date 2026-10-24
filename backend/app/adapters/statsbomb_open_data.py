"""Adapter for the public Hudl/StatsBomb Open Data JSON repository.

The repository contains completed event files, not a live match feed. This
adapter sorts and normalizes those files into the source-independent
``CanonicalEvent`` contract while preserving provider provenance.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.domain.events import CanonicalEvent, EventSource, EventType, Zone


class StatsBombDataError(ValueError):
    """Open Data is missing or cannot be mapped safely."""


@dataclass(frozen=True)
class StatsBombMatch:
    source_match_id: str
    match_id: str
    home_team: str | None
    away_team: str | None
    match_date: str | None
    competition: str | None
    season: str | None
    event_count: int


class StatsBombOpenDataAdapter:
    adapter_name = "statsbomb-open-data"

    def __init__(self, root: str | Path | None = None) -> None:
        configured = root or os.getenv("STATSBOMB_OPEN_DATA_ROOT", "")
        if not configured:
            raise StatsBombDataError("STATSBOMB_OPEN_DATA_ROOT is not configured")
        self.root = Path(configured).expanduser().resolve()
        if not self.root.exists():
            raise StatsBombDataError(f"StatsBomb Open Data root does not exist: {self.root}")

    def list_matches(self, competition_id: int | None = None, season_id: int | None = None) -> list[StatsBombMatch]:
        matches: list[StatsBombMatch] = []
        match_root = self.root / "data" / "matches"
        competition_dirs = [match_root / str(competition_id)] if competition_id is not None else sorted(match_root.glob("*"))
        for competition_dir in competition_dirs:
            season_files = [competition_dir / f"{season_id}.json"] if season_id is not None else sorted(competition_dir.glob("*.json"))
            for season_file in season_files:
                if not season_file.exists():
                    continue
                payload = self._read_json(season_file)
                for match in payload:
                    source_id = str(match.get("match_id"))
                    event_count = len(self._read_json(self._events_path(source_id))) if self._events_path(source_id).exists() else 0
                    matches.append(self._match_summary(match, source_id, event_count))
        return matches

    def load_match(self, source_match_id: str) -> tuple[StatsBombMatch | None, list[CanonicalEvent]]:
        events_path = self._events_path(source_match_id)
        if not events_path.exists():
            raise StatsBombDataError(f"No StatsBomb event file found for match {source_match_id}")
        raw_events = self._read_json(events_path)
        events = [self._normalize_event(item, source_match_id, index) for index, item in enumerate(raw_events)]
        events.sort(key=lambda event: (event.clock_seconds, event.event_id))
        summary = self._find_match_summary(source_match_id, len(events))
        return summary, events

    def _events_path(self, source_match_id: str) -> Path:
        if not source_match_id.isdigit():
            raise StatsBombDataError("source_match_id must be numeric for the Open Data repository")
        return self.root / "data" / "events" / f"{source_match_id}.json"

    def _find_match_summary(self, source_match_id: str, event_count: int) -> StatsBombMatch | None:
        for item in self.list_matches():
            if item.source_match_id == source_match_id:
                return item
        return None

    def _match_summary(self, match: dict[str, Any], source_id: str, event_count: int) -> StatsBombMatch:
        return StatsBombMatch(
            source_match_id=source_id,
            match_id=f"statsbomb_{source_id}",
            home_team=((match.get("home_team") or {}).get("home_team_name")),
            away_team=((match.get("away_team") or {}).get("away_team_name")),
            match_date=match.get("match_date"),
            competition=((match.get("competition") or {}).get("competition_name")),
            season=((match.get("season") or {}).get("season_name")),
            event_count=event_count,
        )

    def _normalize_event(self, raw: dict[str, Any], source_match_id: str, index: int) -> CanonicalEvent:
        event_type_name = str((raw.get("type") or {}).get("name", "Other"))
        event_type = self._event_type(raw, event_type_name)
        location = raw.get("location") or self._nested_location(raw)
        x = round(float(location[0]) / 1.2, 3) if isinstance(location, list) and len(location) >= 2 else None
        y = round(float(location[1]) / 0.8, 3) if isinstance(location, list) and len(location) >= 2 else None
        team = raw.get("team") or {}
        player = raw.get("player") or {}
        attributes = self._attributes(raw, event_type)
        return CanonicalEvent(
            event_id=str(raw.get("id") or f"statsbomb_{source_match_id}_{index}"),
            match_id=f"statsbomb_{source_match_id}",
            minute=int(raw.get("minute") or 0),
            second=min(59, int(raw.get("second") or 0)),
            event_type=event_type,
            team_id=str(team.get("id") or "unknown_team"),
            player_id=str(player["id"]) if player.get("id") is not None else None,
            x=x,
            y=y,
            zone=self._zone(x),
            source=EventSource(
                adapter=self.adapter_name,
                source_event_id=str(raw.get("id") or index),
                raw_metadata={"provider_event_type": event_type_name, "period": raw.get("period"), "match_id": source_match_id},
            ),
            attributes=attributes,
        )

    @staticmethod
    def _event_type(raw: dict[str, Any], name: str) -> EventType:
        if name == "Shot":
            outcome = str(((raw.get("shot") or {}).get("outcome") or {}).get("name", "")).lower()
            return EventType.goal if outcome == "goal" else EventType.shot
        return {
            "Pass": EventType.pass_, "Pressure": EventType.pressure_event,
            "Ball Recovery": EventType.recovery, "Interception": EventType.interception,
            "Tackle": EventType.tackle, "Foul Committed": EventType.foul,
            "Goal Keeper": EventType.recovery, "Dribble": EventType.other,
            "Carry": EventType.other, "Clearance": EventType.recovery,
            "Ball Receipt*": EventType.recovery, "Starting XI": EventType.kickoff,
            "Half End": EventType.half_time, "Substitution": EventType.substitution,
            "Bad Behaviour": EventType.foul,
        }.get(name, EventType.other)

    @staticmethod
    def _attributes(raw: dict[str, Any], event_type: EventType) -> dict[str, Any]:
        if event_type == EventType.pass_:
            passed = raw.get("pass") or {}
            outcome = passed.get("outcome")
            result: dict[str, Any] = {"completed": outcome is None or str(outcome.get("name", "")).lower() == "complete"}
            if (recipient := passed.get("recipient") or {}).get("id") is not None:
                result["recipient_player_id"] = str(recipient["id"])
            return result
        if event_type in (EventType.shot, EventType.goal):
            shot = raw.get("shot") or {}
            outcome = str((shot.get("outcome") or {}).get("name", "")).lower()
            return {"outcome": {"goal": "goal", "saved": "saved", "off target": "off_target", "blocked": "blocked"}.get(outcome, "off_target"), "on_target": outcome in {"goal", "saved"}}
        return {}

    @staticmethod
    def _nested_location(raw: dict[str, Any]) -> list[float] | None:
        for key in ("pass", "shot", "carry", "dribble"):
            value = (raw.get(key) or {}).get("end_location")
            if value:
                return value
        return None

    @staticmethod
    def _zone(x: float | None) -> Zone | None:
        if x is None:
            return None
        if x < 33.3:
            return Zone.defensive_third
        if x < 66.6:
            return Zone.middle_third
        return Zone.attacking_third

    @staticmethod
    def _read_json(path: Path) -> Any:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise StatsBombDataError(f"Unable to read StatsBomb JSON: {path}") from error
