"""Significant moment detection.

Examines the event stream and match state after each event to determine
whether a *significant moment* has occurred that warrants insight generation.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.events import CanonicalEvent, EventType
from app.domain.insights import EvidenceWindow, MetricSnapshot
from app.domain.match_state import MatchClock, MatchState
from app.analytics.rolling_windows import RollingWindowCalculator


@dataclass
class SignificantMoment:
    """A detected moment that should trigger the insight pipeline."""

    moment_type: str  # pressure_shift | goal | red_card | shot_burst | possession_swing
    trigger_event_id: str
    match_clock: MatchClock
    evidence_window: EvidenceWindow
    metrics: list[MetricSnapshot] = field(default_factory=list)


class MomentDetector:
    """Monitors the event stream and fires when a significant moment occurs.

    Significant moment triggers:
        1. Pressure delta > 25 between consecutive 5-min windows
        2. Goal scored
        3. Red card
        4. 3+ shots in a 5-minute window (shot_burst)
        5. Possession swing > 15% between windows

    A per-type cooldown of 3 minutes prevents duplicate triggers.
    """

    COOLDOWN_SECONDS = 180  # 3 minutes

    def __init__(self, rolling: RollingWindowCalculator) -> None:
        self._rolling = rolling
        # moment_type → last trigger total-seconds
        self._last_trigger: dict[str, int] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check(
        self,
        event: CanonicalEvent,
        match_state: MatchState,
    ) -> list[SignificantMoment]:
        """Evaluate whether *event* (just applied to *match_state*) triggers
        any significant moments.

        Returns a (possibly empty) list of detected moments.
        """
        moments: list[SignificantMoment] = []
        clock = MatchClock(minute=event.minute, second=event.second)
        now_seconds = clock.total_seconds()

        # 1. Goal
        if event.event_type == EventType.goal:
            if self._cooldown_ok("goal", now_seconds):
                moments.append(self._build_moment(
                    "goal", event, clock, match_state,
                    window_seconds=60,
                ))
                self._last_trigger["goal"] = now_seconds

        # 2. Red card
        if event.event_type == EventType.red_card:
            if self._cooldown_ok("red_card", now_seconds):
                moments.append(self._build_moment(
                    "red_card", event, clock, match_state,
                    window_seconds=60,
                ))
                self._last_trigger["red_card"] = now_seconds

        # 3. Pressure shift (delta > 25)
        if self._cooldown_ok("pressure_shift", now_seconds):
            moment = self._check_pressure_shift(event, clock, match_state)
            if moment is not None:
                moments.append(moment)
                self._last_trigger["pressure_shift"] = now_seconds

        # 4. Shot burst (3+ shots in 5 min)
        if self._cooldown_ok("shot_burst", now_seconds):
            moment = self._check_shot_burst(event, clock, match_state)
            if moment is not None:
                moments.append(moment)
                self._last_trigger["shot_burst"] = now_seconds

        # 5. Possession swing (> 15 %)
        if self._cooldown_ok("possession_swing", now_seconds):
            moment = self._check_possession_swing(event, clock, match_state)
            if moment is not None:
                moments.append(moment)
                self._last_trigger["possession_swing"] = now_seconds

        return moments

    # ------------------------------------------------------------------
    # Trigger checks
    # ------------------------------------------------------------------

    def _check_pressure_shift(
        self,
        event: CanonicalEvent,
        clock: MatchClock,
        match_state: MatchState,
    ) -> SignificantMoment | None:
        for team_id in match_state.teams:
            pressure, delta, previous = self._rolling.pressure_snapshot(team_id, clock.minute, clock.second)
            if delta is not None and abs(delta) > 25:
                metrics = [
                    MetricSnapshot(name="pressure_index", value=pressure, previous_value=previous, delta=delta, team_id=team_id),
                ]
                return self._build_moment(
                    "pressure_shift", event, clock, match_state,
                    window_seconds=300, extra_metrics=metrics,
                )
        return None

    def _check_shot_burst(
        self,
        event: CanonicalEvent,
        clock: MatchClock,
        match_state: MatchState,
    ) -> SignificantMoment | None:
        for team_id in match_state.teams:
            shot_count = self._rolling.shot_count(team_id, clock.minute, clock.second)
            if shot_count >= 3:
                metrics = [
                    MetricSnapshot(name="shots_in_window", value=float(shot_count), team_id=team_id),
                ]
                return self._build_moment(
                    "shot_burst", event, clock, match_state,
                    window_seconds=300, extra_metrics=metrics,
                )
        return None

    def _check_possession_swing(
        self,
        event: CanonicalEvent,
        clock: MatchClock,
        match_state: MatchState,
    ) -> SignificantMoment | None:
        team_ids = list(match_state.teams.keys())
        if len(team_ids) < 2:
            return None

        for team_id in team_ids:
            current = self._rolling.get_events_in_window(
                team_id, clock.minute, clock.second, 300,
            )
            previous = self._rolling.get_previous_window_events(
                team_id, clock.minute, clock.second, 300,
            )
            current_poss = self._possession_pct(current, team_id, clock, 300, is_current=True)
            previous_poss = self._possession_pct(previous, team_id, clock, 300, is_current=False)

            if previous_poss is not None and abs(current_poss - previous_poss) > 15:
                metrics = [
                    MetricSnapshot(
                        name="possession_pct",
                        value=current_poss,
                        previous_value=previous_poss,
                        delta=current_poss - previous_poss,
                        team_id=team_id,
                    ),
                ]
                return self._build_moment(
                    "possession_swing", event, clock, match_state,
                    window_seconds=300, extra_metrics=metrics,
                )
        return None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _cooldown_ok(self, moment_type: str, now_seconds: int) -> bool:
        last = self._last_trigger.get(moment_type)
        if last is None:
            return True
        return (now_seconds - last) >= self.COOLDOWN_SECONDS

    def _build_moment(
        self,
        moment_type: str,
        trigger_event: CanonicalEvent,
        clock: MatchClock,
        match_state: MatchState,
        window_seconds: int = 300,
        extra_metrics: list[MetricSnapshot] | None = None,
    ) -> SignificantMoment:
        start_total = max(0, clock.total_seconds() - window_seconds)
        start_min = start_total // 60
        start_sec = start_total % 60

        window_event_ids = [
            item.event_id for item in self._rolling.get_all_events_in_window(
                clock.minute, clock.second, window_seconds,
            )
        ]

        evidence = EvidenceWindow(
            start_minute=start_min,
            start_second=start_sec,
            end_minute=clock.minute,
            end_second=clock.second,
            event_ids=window_event_ids,
        )

        return SignificantMoment(
            moment_type=moment_type,
            trigger_event_id=trigger_event.event_id,
            match_clock=clock,
            evidence_window=evidence,
            metrics=extra_metrics or [],
        )

    def _possession_pct(
        self,
        events: list[CanonicalEvent],
        team_id: str,
        clock: MatchClock,
        window_seconds: int,
        is_current: bool,
    ) -> float | None:
        """Estimate possession % for *team_id* from event counts in a window.

        Uses a simple ratio of team events to total events in the window.
        """
        if is_current:
            all_events = self._rolling.get_all_events_in_window(
                clock.minute, clock.second, window_seconds,
            )
        else:
            end_total = clock.minute * 60 + clock.second
            prev_end = max(0, end_total - window_seconds)
            prev_start = max(0, prev_end - window_seconds)
            all_events = [
                e for e in self._rolling.events
                if prev_start <= e.clock_seconds < prev_end
            ]

        if not all_events:
            return None

        team_count = sum(1 for e in all_events if e.team_id == team_id)
        return (team_count / len(all_events)) * 100
