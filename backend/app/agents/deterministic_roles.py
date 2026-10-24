"""Local, typed role implementations used until Foundry is configured.

They are intentionally distinct computational roles rather than renamed prompt
templates. They consume immutable evidence facts and return bounded structured
findings. No role calculates authoritative match metrics.
"""

from __future__ import annotations

from collections import Counter

from app.agents.contracts import EvidenceContext, MatchAnalysisOutput, TacticalAnalysisOutput
from app.domain.insights import AgentFinding, AgentStage, AgentStatus


class DeterministicMatchAnalyst:
    def analyze(self, context: EvidenceContext) -> MatchAnalysisOutput:
        measured = [
            {
                "name": metric.name,
                "value": metric.value,
                "previous_value": metric.previous_value,
                "delta": metric.delta,
                "team_id": metric.team_id,
                "definition_version": metric.definition_version,
            }
            for metric in context.metrics
        ]
        return MatchAnalysisOutput(
            finding=AgentFinding(
                agent_name="deterministic_match_analyst",
                stage=AgentStage.match_analyst,
                status=AgentStatus.success,
                findings={
                    "observations": measured,
                    "interpretations": [],
                    "caveats": ["Metrics are supplied by the deterministic engine and are not recalculated by this role."],
                },
                event_ids=list(context.event_ids),
                input_state_version=context.match_state_version,
            )
        )


class DeterministicTacticalAnalyst:
    def analyze(self, context: EvidenceContext) -> TacticalAnalysisOutput:
        event_counts = dict(Counter(context.event_types))
        zone_counts = dict(Counter(context.zones))
        caveats = [
            "This is a low-confidence, evidence-bounded hypothesis rather than a claim of tactical intent.",
        ]
        hypothesis: str | None = None
        if zone_counts.get("attacking_third", 0) >= 2:
            hypothesis = "The evidence window contains repeated recorded activity in the attacking third."
        else:
            caveats.append("Insufficient territorial evidence to infer a tactical pattern.")
        return TacticalAnalysisOutput(
            finding=AgentFinding(
                agent_name="deterministic_tactical_analyst",
                stage=AgentStage.tactical_analyst,
                status=AgentStatus.success,
                findings={
                    "hypothesis": hypothesis,
                    "event_type_counts": event_counts,
                    "zone_counts": zone_counts,
                    "confidence": "low" if hypothesis else "insufficient_evidence",
                    "caveats": caveats,
                },
                event_ids=list(context.event_ids),
                input_state_version=context.match_state_version,
            )
        )
