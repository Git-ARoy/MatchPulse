"""In-memory application service for the first event-to-insight vertical slice.

This is an intentionally replaceable local persistence adapter. It owns the
match-scoped event ledger and coordinates deterministic processing; it does not
pretend to be a durable Cosmos DB implementation.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from app.analytics.evidence_builder import EvidenceBuilder, EvidencePackage
from app.analytics.match_tracker import MatchTracker
from app.analytics.moment_detector import MomentDetector
from app.analytics.rolling_windows import RollingWindowCalculator
from app.domain.events import CanonicalEvent
from app.domain.analysis_runs import AnalysisOutcome, AnalysisRun
from app.domain.insights import Insight
from app.domain.match_state import MatchState
from app.orchestration.coordinator import AgentCoordinator
from app.services.redis_cache import RedisMatchCache


class EventConflictError(ValueError):
    """An event ID is already associated with a different canonical payload."""


class EventOrderError(ValueError):
    """An event arrived earlier than an already processed match-clock event."""


class MatchNotFoundError(KeyError):
    """No events have been received for the requested match."""


class InsightNotFoundError(KeyError):
    """No published insight has the requested ID."""


@dataclass
class IngestionOutcome:
    accepted: bool
    duplicate: bool
    state_version: int
    published_insights: list[Insight] = field(default_factory=list)
    analysis_run_ids: list[str] = field(default_factory=list)


@dataclass
class MatchSession:
    match_id: str
    tracker: MatchTracker = field(init=False)
    rolling: RollingWindowCalculator = field(default_factory=RollingWindowCalculator)
    events: list[CanonicalEvent] = field(default_factory=list)
    events_by_id: dict[str, CanonicalEvent] = field(default_factory=dict)
    insights: list[Insight] = field(default_factory=list)
    evidence: dict[str, EvidencePackage] = field(default_factory=dict)
    analysis_runs: dict[str, AnalysisRun] = field(default_factory=dict)
    detector: MomentDetector = field(init=False)

    def __post_init__(self) -> None:
        self.tracker = MatchTracker(self.match_id)
        self.detector = MomentDetector(self.rolling)


class MatchService:
    """Coordinates validation results with deterministic match intelligence."""

    def __init__(self) -> None:
        self._sessions: dict[str, MatchSession] = {}
        self._event_match_ids: dict[str, str] = {}
        self._insight_index: dict[str, Insight] = {}
        self._evidence_index: dict[str, EvidencePackage] = {}
        self._run_index: dict[str, AnalysisRun] = {}
        self._coordinator = AgentCoordinator()
        self._cache = RedisMatchCache()

    def ingest(self, event: CanonicalEvent) -> IngestionOutcome:
        known_match_id = self._event_match_ids.get(event.event_id)
        if known_match_id is not None and known_match_id != event.match_id:
            raise EventConflictError("event_id is already associated with another match")

        session = self._sessions.setdefault(event.match_id, MatchSession(event.match_id))
        normalized = session.tracker.normalize_event(event)
        existing = session.events_by_id.get(normalized.event_id)
        if existing is not None:
            if existing.model_dump(mode="json") == normalized.model_dump(mode="json"):
                return IngestionOutcome(False, True, session.tracker.state.state_version)
            raise EventConflictError("event_id already exists with a different canonical payload")

        if session.events and normalized.clock_seconds < session.events[-1].clock_seconds:
            raise EventOrderError("out-of-order events are rejected by the inline processor; replay in chronological order")

        processed = session.tracker.process_event(normalized)
        if not processed.accepted:
            raise EventConflictError(processed.message)

        session.events.append(normalized)
        session.events_by_id[normalized.event_id] = normalized
        self._event_match_ids[normalized.event_id] = normalized.match_id
        session.rolling.add_event(normalized)

        published: list[Insight] = []
        run_ids: list[str] = []
        for moment in session.detector.check(normalized, session.tracker.state):
            package = EvidenceBuilder(session.rolling, session.events).build(moment, session.tracker.state)
            session.evidence[package.evidence_id] = package
            self._evidence_index[package.evidence_id] = package
            run = self._coordinator.run(moment, session.tracker.state, package)
            analysis_run = AnalysisRun(
                run_id=f"run_{uuid.uuid4().hex}",
                match_id=session.match_id,
                evidence_id=package.evidence_id,
                match_state_version=session.tracker.state.state_version,
                outcome=AnalysisOutcome(run.outcome),
                insight_ids=[run.insight.insight_id] if run.insight else [],
                stages=run.findings,
                validation=run.validation,
                duration_ms=run.duration_ms,
            )
            session.analysis_runs[analysis_run.run_id] = analysis_run
            self._run_index[analysis_run.run_id] = analysis_run
            run_ids.append(analysis_run.run_id)
            if run.insight is None:
                continue
            insight = run.insight
            session.insights.append(insight)
            self._insight_index[insight.insight_id] = insight
            published.append(insight)
        self._cache.write(
            event.match_id,
            self.get_state_view(event.match_id),
            [item.model_dump(mode="json") for item in session.insights],
        )
        return IngestionOutcome(True, False, session.tracker.state.state_version, published, run_ids)

    def get_state(self, match_id: str) -> MatchState:
        return self._session(match_id).tracker.state

    def get_state_view(self, match_id: str) -> dict:
        """Return deterministic state plus currently computable metric values."""
        session = self._session(match_id)
        state = session.tracker.state
        payload = state.model_dump(mode="json")
        metrics: dict[str, dict] = {}
        for team_id in state.teams:
            current = session.rolling.get_events_in_window(
                team_id, state.match_clock.minute, state.match_clock.second,
            )
            previous = session.rolling.get_previous_window_events(
                team_id, state.match_clock.minute, state.match_clock.second,
            )
            value, delta = session.rolling.calculate_pressure_index(team_id, current, previous)
            previous_value = None
            if previous:
                previous_value, _ = session.rolling.calculate_pressure_index(team_id, previous)
            metrics[f"pressure_index:{team_id}"] = {
                "team_id": team_id,
                "value": value,
                "previous_window_value": previous_value,
                "delta": delta,
                "window_seconds": 300,
                "previous_window_seconds": 300,
                "definition_version": "pressure-v1",
                "availability": "available" if current else "insufficient_events",
            }
        payload["metrics"] = metrics
        return payload

    def list_insights(self, match_id: str, limit: int, after: str | None) -> tuple[list[Insight], str | None]:
        items = self._session(match_id).insights
        start = 0
        if after:
            ids = [item.insight_id for item in items]
            if after not in ids:
                raise InsightNotFoundError("cursor does not identify an insight in this match")
            start = ids.index(after) + 1
        page = items[start:start + limit]
        next_cursor = page[-1].insight_id if start + len(page) < len(items) else None
        return page, next_cursor

    def list_events(self, match_id: str, limit: int, after: str | None) -> tuple[list[CanonicalEvent], str | None]:
        """Return the canonical ledger in the order accepted by the processor."""
        items = self._session(match_id).events
        start = 0
        if after:
            ids = [item.event_id for item in items]
            if after not in ids:
                raise InsightNotFoundError("cursor does not identify an event in this match")
            start = ids.index(after) + 1
        page = items[start:start + limit]
        next_cursor = page[-1].event_id if start + len(page) < len(items) else None
        return page, next_cursor

    def has_events(self, match_id: str) -> bool:
        """Whether a session has an accepted event; used by dev-only fixtures."""
        session = self._sessions.get(match_id)
        return bool(session and session.events)

    def get_insight(self, insight_id: str) -> Insight:
        try:
            return self._insight_index[insight_id]
        except KeyError as error:
            raise InsightNotFoundError("insight not found") from error

    def get_evidence(self, insight_id: str) -> EvidencePackage:
        insight = self.get_insight(insight_id)
        return self._evidence_index[insight.evidence_id]

    def get_analysis_run(self, run_id: str) -> AnalysisRun:
        try:
            return self._run_index[run_id]
        except KeyError as error:
            raise InsightNotFoundError("analysis run not found") from error

    def _session(self, match_id: str) -> MatchSession:
        try:
            return self._sessions[match_id]
        except KeyError as error:
            raise MatchNotFoundError("match not found") from error
