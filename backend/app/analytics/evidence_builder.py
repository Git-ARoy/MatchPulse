"""Evidence builder – constructs immutable evidence packages.

Given a :class:`SignificantMoment`, the evidence builder filters the event
stream to exactly the events inside the declared time window and assembles
before / after metric snapshots.
"""

from __future__ import annotations

from dataclasses import dataclass
import uuid

from app.domain.events import CanonicalEvent
from app.domain.insights import EvidenceWindow, MetricSnapshot
from app.domain.match_state import MatchState
from app.analytics.moment_detector import SignificantMoment
from app.analytics.rolling_windows import RollingWindowCalculator


@dataclass
class EvidencePackage:
    """Immutable evidence bundle consumed by agents."""

    moment: SignificantMoment
    evidence_window: EvidenceWindow
    events_in_window: list[CanonicalEvent]
    metrics: list[MetricSnapshot]
    match_state_version: int
    evidence_id: str


class EvidenceBuilder:
    """Construct evidence packages for significant moments."""

    def __init__(
        self,
        rolling: RollingWindowCalculator,
        all_events: list[CanonicalEvent],
    ) -> None:
        self._rolling = rolling
        self._all_events = all_events

    def build(
        self,
        moment: SignificantMoment,
        match_state: MatchState,
    ) -> EvidencePackage:
        """Build a fully-resolved evidence package for *moment*.

        1. Filter events to the declared evidence window.
        2. Compute before / after metric snapshots.
        3. Return an immutable :class:`EvidencePackage`.
        """
        window = moment.evidence_window
        start_total = window.start_minute * 60 + window.start_second
        end_total = window.end_minute * 60 + window.end_second

        events_in_window = [
            ev for ev in self._all_events
            if start_total <= (ev.minute * 60 + ev.second) <= end_total
        ]

        # Update the evidence window with precise event IDs
        precise_window = EvidenceWindow(
            start_minute=window.start_minute,
            start_second=window.start_second,
            end_minute=window.end_minute,
            end_second=window.end_second,
            event_ids=[ev.event_id for ev in events_in_window],
        )

        # Build metrics – include moment metrics + team stat snapshots
        metrics = list(moment.metrics)
        for team_id, ts in match_state.teams.items():
            metrics.extend([
                MetricSnapshot(name="goals", value=float(ts.goals), team_id=team_id),
                MetricSnapshot(name="shots", value=float(ts.shots), team_id=team_id),
                MetricSnapshot(name="passes", value=float(ts.passes), team_id=team_id),
                MetricSnapshot(name="possession_events", value=float(ts.possession_events), team_id=team_id),
            ])

        return EvidencePackage(
            moment=moment,
            evidence_window=precise_window,
            events_in_window=events_in_window,
            metrics=metrics,
            match_state_version=match_state.state_version,
            evidence_id=f"evidence_{uuid.uuid4().hex}",
        )
