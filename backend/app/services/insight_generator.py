"""Deterministic insight generator.

Generates audience-adapted insights from significant moments using
template-based narratives.  This module is the fallback path when AI agents
are unavailable and also serves as the reference implementation for insight
structure.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from app.domain.events import CanonicalEvent
from app.domain.insights import (
    AudienceMode,
    AudienceVariant,
    EvidenceWindow,
    Insight,
    InsightStatus,
    InsightType,
    MetricSnapshot,
    ValidationResult,
)
from app.domain.match_state import MatchState
from app.analytics.evidence_builder import EvidencePackage
from app.analytics.moment_detector import SignificantMoment


_INSIGHT_TYPE_MAP: dict[str, InsightType] = {
    "pressure_shift": InsightType.pressure_shift,
    "goal": InsightType.goal,
    "red_card": InsightType.red_card,
    "shot_burst": InsightType.shot_burst,
    "possession_swing": InsightType.possession_swing,
}


class InsightGenerator:
    """Generate fully-formed :class:`Insight` objects from evidence packages."""

    def generate(
        self,
        moment: SignificantMoment,
        match_state: MatchState,
        evidence: EvidencePackage,
        validation: ValidationResult | None = None,
    ) -> Insight:
        """Produce an insight with audience variants for the given moment."""
        insight_type = _INSIGHT_TYPE_MAP.get(moment.moment_type, InsightType.pressure_shift)
        team_id = self._primary_team(evidence)
        team_label = team_id or "Unknown"

        headline = self._headline(moment, team_label, evidence)
        summary = self._summary(moment, team_label, evidence)
        what_changed = self._what_changed(moment, team_label, evidence)
        why_it_matters = self._why_it_matters(moment, team_label, evidence)

        audience_variants = {
            "fan": self._fan_variant(moment, team_label, evidence),
            "analyst": self._analyst_variant(moment, team_label, evidence, match_state),
            "broadcast": self._broadcast_variant(moment, team_label, evidence),
        }

        return Insight(
            insight_id=str(uuid.uuid4()),
            evidence_id=evidence.evidence_id,
            version=1,
            match_id=match_state.match_id,
            match_state_version=match_state.state_version,
            match_clock={"minute": moment.match_clock.minute, "second": moment.match_clock.second},
            insight_type=insight_type,
            headline=headline,
            summary=summary,
            what_changed=what_changed,
            why_it_matters=why_it_matters,
            evidence=evidence.evidence_window,
            metrics=evidence.metrics,
            source_event_ids=[ev.event_id for ev in evidence.events_in_window],
            agent_findings=[],
            validation=validation,
            audience_variants=audience_variants,
            status=InsightStatus.verified if validation is None or validation.status.value in ("approved", "repaired") else InsightStatus.fallback,
            created_at=datetime.now(UTC),
        )

    # ------------------------------------------------------------------
    # Templates per moment type
    # ------------------------------------------------------------------

    def _headline(self, moment: SignificantMoment, team: str, evidence: EvidencePackage) -> str:
        templates = {
            "pressure_shift": f"{team} surge – pressure index spikes",
            "goal": f"GOAL! {team} find the net",
            "red_card": f"Red card – {team} reduced to 10",
            "shot_burst": f"{team} unleash a flurry of shots",
            "possession_swing": f"Momentum shift – {team} seize control",
        }
        return templates.get(moment.moment_type, f"Notable moment – {team}")

    def _summary(self, moment: SignificantMoment, team: str, evidence: EvidencePackage) -> str:
        n_events = len(evidence.events_in_window)
        window_start = f"{evidence.evidence_window.start_minute}'"
        window_end = f"{evidence.evidence_window.end_minute}'"

        templates = {
            "pressure_shift": (
                f"Between {window_start} and {window_end}, {team} generated "
                f"{n_events} events with a marked increase in attacking intensity. "
                f"The pressure index rose significantly compared to the preceding window."
            ),
            "goal": (
                f"{team} scored at {moment.match_clock.minute}'{moment.match_clock.second:02d}\". "
                f"The evidence window contains {n_events} recorded event(s)."
            ),
            "red_card": (
                f"A red card was shown to a {team} player at {moment.match_clock.minute}'"
                f"{moment.match_clock.second:02d}\". The match dynamic shifts with "
                f"The evidence record should be reviewed alongside subsequent events."
            ),
            "shot_burst": (
                f"{team} fired multiple shots in a 5-minute window ending at "
                f"{window_end}. A total of {n_events} attacking events were "
                f"recorded in this passage."
            ),
            "possession_swing": (
                f"Possession swung markedly towards {team} between {window_start} "
                f"and {window_end}. The calculation is based on recorded event volume."
            ),
        }
        return templates.get(moment.moment_type, f"A notable moment involving {team} at {window_end}.")

    def _what_changed(self, moment: SignificantMoment, team: str, evidence: EvidencePackage) -> str:
        metric_parts: list[str] = []
        for m in moment.metrics:
            if m.delta is not None:
                metric_parts.append(f"{m.name}: {m.value:.1f} (Δ{m.delta:+.1f})")
            else:
                metric_parts.append(f"{m.name}: {m.value:.1f}")
        metric_str = "; ".join(metric_parts) if metric_parts else "See metrics"

        templates = {
            "pressure_shift": f"{team}'s attacking output surged. {metric_str}.",
            "goal": f"The scoreline changed. {team} scored.",
            "red_card": f"{team} lost a player to a red card, shifting the balance.",
            "shot_burst": f"{team} created a burst of shots. {metric_str}.",
            "possession_swing": f"Ball retention shifted towards {team}. {metric_str}.",
        }
        return templates.get(moment.moment_type, f"Key change for {team}. {metric_str}.")

    def _why_it_matters(self, moment: SignificantMoment, team: str, evidence: EvidencePackage) -> str:
        templates = {
            "pressure_shift": (
                f"The measured pressure index increased. This is a MatchPulse "
                f"signal to monitor, not evidence of a specific tactical cause."
            ),
            "goal": (
                f"The score changed. Subsequent events are needed before inferring "
                f"a tactical response."
            ),
            "red_card": (
                f"The dismissal is a recorded match-state change; no tactical "
                f"conclusion is asserted without subsequent evidence."
            ),
            "shot_burst": (
                f"The shot count met the configured burst threshold. Shot quality "
                f"and future outcomes are not inferred from this count alone."
            ),
            "possession_swing": (
                f"The event-volume possession proxy changed. It is not a conclusion "
                f"about tactical intent or ball-time possession."
            ),
        }
        return templates.get(moment.moment_type, f"This moment could influence the match outcome.")

    # ------------------------------------------------------------------
    # Audience variants
    # ------------------------------------------------------------------

    def _fan_variant(
        self, moment: SignificantMoment, team: str, evidence: EvidencePackage,
    ) -> AudienceVariant:
        """Fan-facing: accessible language, emotional context, team-focused."""
        templates = {
            "pressure_shift": {
                "headline": f"🔥 {team} are turning up the heat!",
                "summary": (
                    f"{team} are piling on the pressure! They've been camped "
                    f"in the opposition half with wave after wave of attacks. "
                    f"The momentum is firmly with them right now."
                ),
                "why_it_matters": (
                    f"When a team creates this much pressure, a goal often follows. "
                    f"Keep your eyes glued to the screen!"
                ),
                "next_watch": f"Watch for {team}'s next chance – could be the breakthrough.",
            },
            "goal": {
                "headline": f"⚽ {team} SCORE!",
                "summary": (
                    f"GET IN! {team} have found the back of the net! "
                    f"What a moment at {moment.match_clock.minute}' – the fans are on their feet!"
                ),
                "why_it_matters": "Every goal changes the game. The opposition now has to respond.",
                "next_watch": "Will the opposition push for an equaliser or sit deeper?",
            },
            "red_card": {
                "headline": f"🟥 {team} down to 10!",
                "summary": (
                    f"Drama! A {team} player has been sent off. "
                    f"They'll have to dig deep to compete with 10 players."
                ),
                "why_it_matters": "Playing a player short is a huge disadvantage – expect tactical changes.",
                "next_watch": "Watch for a substitution and a shift in formation.",
            },
            "shot_burst": {
                "headline": f"🎯 {team} are shooting on sight!",
                "summary": (
                    f"{team} have peppered the goal with shots in a short spell. "
                    f"The goalkeeper is being kept very busy!"
                ),
                "why_it_matters": "This many chances means a goal could be coming at any moment!",
                "next_watch": f"Can {team} convert one of these chances?",
            },
            "possession_swing": {
                "headline": f"🔄 {team} take charge of the ball!",
                "summary": (
                    f"The tide has turned! {team} are now dominating possession "
                    f"after a period of being on the back foot."
                ),
                "why_it_matters": "Controlling the ball means controlling the game – this is a key shift.",
                "next_watch": "See if this possession leads to clear-cut chances.",
            },
        }
        t = templates.get(moment.moment_type, {
            "headline": f"📋 Notable moment for {team}",
            "summary": f"Something significant happened involving {team}.",
            "why_it_matters": "This could influence the match.",
            "next_watch": "Keep watching for developments.",
        })
        return AudienceVariant(
            mode=AudienceMode.fan,
            headline=t["headline"],
            summary=t["summary"],
            why_it_matters=t["why_it_matters"],
            next_watch=t.get("next_watch"),
        )

    def _analyst_variant(
        self,
        moment: SignificantMoment,
        team: str,
        evidence: EvidencePackage,
        match_state: MatchState,
    ) -> AudienceVariant:
        """Analyst-facing: detailed metrics, before/after, event sequences."""
        window = evidence.evidence_window
        n_events = len(evidence.events_in_window)

        # Build metric detail string
        metric_lines: list[str] = []
        for m in evidence.metrics:
            parts = [f"{m.name}={m.value:.1f}"]
            if m.previous_value is not None:
                parts.append(f"prev={m.previous_value:.1f}")
            if m.delta is not None:
                parts.append(f"Δ={m.delta:+.1f}")
            if m.team_id:
                parts.append(f"[{m.team_id}]")
            metric_lines.append(", ".join(parts))
        metric_block = "\n".join(f"  • {line}" for line in metric_lines) if metric_lines else "  (no metrics)"

        # Team state summary
        team_states: list[str] = []
        for tid, ts in match_state.teams.items():
            team_states.append(
                f"  {tid}: G={ts.goals} S={ts.shots} SOT={ts.shots_on_target} "
                f"P={ts.passes} INT={ts.interceptions} T={ts.tackles} "
                f"HR={ts.high_regains} ATE={ts.attacking_third_entries} PBE={ts.penalty_box_entries}"
            )
        team_block = "\n".join(team_states)

        detail = (
            f"Evidence window: {window.start_minute}'{window.start_second:02d}\" – "
            f"{window.end_minute}'{window.end_second:02d}\"\n"
            f"Events in window: {n_events}\n"
            f"Event IDs: {', '.join(window.event_ids[:10])}"
            f"{'...' if len(window.event_ids) > 10 else ''}\n\n"
            f"Metrics:\n{metric_block}\n\n"
            f"Team state (at v{match_state.state_version}):\n{team_block}"
        )

        return AudienceVariant(
            mode=AudienceMode.analyst,
            headline=f"[{moment.moment_type.upper()}] {team} – {moment.match_clock.minute}'",
            summary=(
                f"Significant {moment.moment_type.replace('_', ' ')} detected at "
                f"{moment.match_clock.minute}'{moment.match_clock.second:02d}\" involving {team}. "
                f"{n_events} events in the evidence window across "
                f"{window.end_minute - window.start_minute} minutes."
            ),
            why_it_matters=(
                f"Pattern indicates a measurable shift in match dynamics. "
                f"Recommend monitoring for follow-on events within the next 5 minutes."
            ),
            detail=detail,
            next_watch=(
                f"Track {team}'s output in the next 300 s window for momentum continuation."
            ),
        )

    def _broadcast_variant(
        self, moment: SignificantMoment, team: str, evidence: EvidencePackage,
    ) -> AudienceVariant:
        """Broadcast-facing: compact, structured for overlay rendering."""
        key_metric = ""
        if moment.metrics:
            m = moment.metrics[0]
            if m.delta is not None:
                key_metric = f"{m.name}: {m.value:.0f} ({m.delta:+.0f})"
            else:
                key_metric = f"{m.name}: {m.value:.0f}"

        templates = {
            "pressure_shift": {
                "headline": f"PRESSURE SURGE – {team.upper()}",
                "summary": f"{team} intensity ↑ | {key_metric}" if key_metric else f"{team} intensity ↑",
            },
            "goal": {
                "headline": f"GOAL – {team.upper()}",
                "summary": f"{moment.match_clock.minute}' | {team} score",
            },
            "red_card": {
                "headline": f"RED CARD – {team.upper()}",
                "summary": f"{moment.match_clock.minute}' | {team} → 10 players",
            },
            "shot_burst": {
                "headline": f"SHOT BURST – {team.upper()}",
                "summary": f"{team} | {key_metric}" if key_metric else f"{team} | multiple shots",
            },
            "possession_swing": {
                "headline": f"POSSESSION SHIFT – {team.upper()}",
                "summary": f"{team} | {key_metric}" if key_metric else f"{team} | dominance shift",
            },
        }
        t = templates.get(moment.moment_type, {
            "headline": f"KEY MOMENT – {team.upper()}",
            "summary": f"{team} | {moment.match_clock.minute}'",
        })
        return AudienceVariant(
            mode=AudienceMode.broadcast,
            headline=t["headline"],
            summary=t["summary"],
            why_it_matters=key_metric or "Significant tactical shift detected.",
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _primary_team(evidence: EvidencePackage) -> str:
        """Determine the primary team for the moment from metrics or events."""
        # Try metrics first
        for m in evidence.moment.metrics:
            if m.team_id:
                return m.team_id
        # Fall back to the most common team in evidence events
        if evidence.events_in_window:
            from collections import Counter
            counts = Counter(ev.team_id for ev in evidence.events_in_window)
            return counts.most_common(1)[0][0]
        return "Unknown"
