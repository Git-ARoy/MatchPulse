"""Microsoft Agent Framework-based coordinator for MatchPulse analysis runs."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass

from agent_framework import step, workflow

from app.agents.contracts import EvidenceContext
from app.agents.deterministic_roles import DeterministicMatchAnalyst, DeterministicTacticalAnalyst
from app.agents.foundry_provider import FoundryNarrativeProducer, FoundryUnavailableError
from app.analytics.evidence_builder import EvidencePackage
from app.analytics.moment_detector import SignificantMoment
from app.domain.insights import AgentFinding, AgentStage, AgentStatus, Insight, InsightStatus, ValidationResult, ValidationStatus
from app.domain.match_state import MatchState
from app.services.evidence_auditor import EvidenceAuditor
from app.services.insight_generator import InsightGenerator


@dataclass(frozen=True)
class OrchestrationRequest:
    """Run-scoped input; all role stages refer to this same state version."""

    moment: SignificantMoment
    match_state: MatchState
    evidence: EvidencePackage


@dataclass
class OrchestrationResult:
    insight: Insight | None
    validation: ValidationResult
    findings: list[AgentFinding]
    outcome: str
    duration_ms: float


def _context(request: OrchestrationRequest) -> EvidenceContext:
    return EvidenceContext(
        match_id=request.match_state.match_id,
        match_state_version=request.match_state.state_version,
        moment_type=request.moment.moment_type,
        trigger_event_id=request.moment.trigger_event_id,
        match_clock={"minute": request.moment.match_clock.minute, "second": request.moment.match_clock.second},
        evidence_id=request.evidence.evidence_id,
        event_ids=tuple(event.event_id for event in request.evidence.events_in_window),
        event_types=tuple(event.event_type.value for event in request.evidence.events_in_window),
        zones=tuple(event.zone.value for event in request.evidence.events_in_window if event.zone is not None),
        metrics=tuple(request.evidence.metrics),
        team_state={team_id: team.model_dump(exclude={"team_id"}) for team_id, team in request.match_state.teams.items()},
    )


@step(name="match_analyst", replay_key=lambda context: context.evidence_id)
async def run_match_analyst(context: EvidenceContext) -> AgentFinding:
    started = time.perf_counter()
    output = DeterministicMatchAnalyst().analyze(context).finding
    output.duration_ms = (time.perf_counter() - started) * 1000
    return output


@step(name="tactical_analyst", replay_key=lambda context: context.evidence_id)
async def run_tactical_analyst(context: EvidenceContext) -> AgentFinding:
    started = time.perf_counter()
    output = DeterministicTacticalAnalyst().analyze(context).finding
    output.duration_ms = (time.perf_counter() - started) * 1000
    return output


@workflow(name="matchpulse_analysis", description="Run distinct MatchPulse specialist stages against one evidence snapshot.")
async def matchpulse_analysis(request: OrchestrationRequest) -> OrchestrationResult:
    """Fan out the two independent specialists, then produce and audit a story."""
    context = _context(request)
    match_finding, tactical_finding = await asyncio.gather(
        run_match_analyst(context),
        run_tactical_analyst(context),
    )
    findings = [match_finding, tactical_finding]

    generator = InsightGenerator()
    producer_started = time.perf_counter()
    insight = generator.generate(request.moment, request.match_state, request.evidence)
    producer_name = "deterministic_narrative_producer"
    producer_status = AgentStatus.success
    producer_findings: dict[str, object] = {"insight_id": insight.insight_id, "evidence_id": insight.evidence_id, "provider": "deterministic"}
    try:
        foundry = FoundryNarrativeProducer.from_environment()
        if foundry is not None:
            narrative = await foundry.produce(context)
            insight = insight.model_copy(update={
                "headline": narrative.headline,
                "summary": narrative.summary,
                "what_changed": narrative.what_changed,
                "why_it_matters": narrative.why_it_matters,
            })
            producer_name = "foundry_narrative_producer"
            producer_findings = {"insight_id": insight.insight_id, "evidence_id": insight.evidence_id, "provider": "microsoft_foundry", "model": foundry.model}
    except FoundryUnavailableError as error:
        # A provider error is non-fatal. The deterministic template is the
        # safe fallback and its reason remains visible in the run trace.
        producer_status = AgentStatus.success
        producer_findings["foundry_fallback_reason"] = str(error)
    findings.append(AgentFinding(
        agent_name=producer_name,
        stage=AgentStage.narrative_producer,
        status=producer_status,
        findings=producer_findings,
        event_ids=insight.source_event_ids,
        input_state_version=request.match_state.state_version,
        duration_ms=(time.perf_counter() - producer_started) * 1000,
    ))

    auditor_started = time.perf_counter()
    validation = EvidenceAuditor().validate(request.evidence, request.match_state, insight)
    findings.append(AgentFinding(
        agent_name="deterministic_evidence_auditor",
        stage=AgentStage.evidence_auditor,
        status=AgentStatus.success if validation.status == ValidationStatus.approved else AgentStatus.failure,
        findings={"status": validation.status.value, "checks": [check.model_dump() for check in validation.checks]},
        event_ids=insight.source_event_ids,
        input_state_version=request.match_state.state_version,
        duration_ms=(time.perf_counter() - auditor_started) * 1000,
    ))

    if validation.status != ValidationStatus.approved:
        # A rejected candidate never reaches the UI. The one permitted repair
        # regenerates it from the immutable deterministic evidence snapshot;
        # it cannot change metrics, IDs, or the evidence window.
        repair_started = time.perf_counter()
        repaired = generator.generate(request.moment, request.match_state, request.evidence)
        repaired_validation = EvidenceAuditor().validate(request.evidence, request.match_state, repaired)
        findings.append(AgentFinding(
            agent_name="deterministic_narrative_repair",
            stage=AgentStage.narrative_producer,
            status=AgentStatus.success if repaired_validation.status == ValidationStatus.approved else AgentStatus.failure,
            findings={"attempt": 1, "reason": "initial evidence audit rejected candidate", "insight_id": repaired.insight_id},
            event_ids=repaired.source_event_ids,
            input_state_version=request.match_state.state_version,
            duration_ms=(time.perf_counter() - repair_started) * 1000,
        ))
        findings.append(AgentFinding(
            agent_name="deterministic_evidence_auditor",
            stage=AgentStage.evidence_auditor,
            status=AgentStatus.success if repaired_validation.status == ValidationStatus.approved else AgentStatus.failure,
            findings={"attempt": 1, "status": repaired_validation.status.value, "checks": [check.model_dump() for check in repaired_validation.checks]},
            event_ids=repaired.source_event_ids,
            input_state_version=request.match_state.state_version,
            duration_ms=0.0,
        ))
        if repaired_validation.status == ValidationStatus.approved:
            repaired_validation = repaired_validation.model_copy(update={
                "status": ValidationStatus.repaired,
                "repair_count": 1,
                "semantic_findings": ["Initial candidate was rejected; one evidence-locked repair passed."],
            })
            return OrchestrationResult(
                repaired.model_copy(update={"agent_findings": findings, "validation": repaired_validation}),
                repaired_validation,
                findings,
                "insight_published",
                0.0,
            )

        # The safe fallback is the same deterministic, evidence-locked
        # template route. Publish only if the raw evidence package itself is
        # still auditable. Otherwise suppression is the only safe outcome.
        baseline_validation = EvidenceAuditor().validate(request.evidence, request.match_state)
        if baseline_validation.status == ValidationStatus.approved:
            fallback = generator.generate(request.moment, request.match_state, request.evidence)
            fallback_validation = EvidenceAuditor().validate(request.evidence, request.match_state, fallback)
            if fallback_validation.status == ValidationStatus.approved:
                fallback_validation = fallback_validation.model_copy(update={
                    "status": ValidationStatus.fallback,
                    "repair_count": 1,
                    "semantic_findings": ["Candidate and repair were rejected; deterministic evidence-locked fallback was published."],
                })
                findings.append(AgentFinding(
                    agent_name="deterministic_safe_fallback",
                    stage=AgentStage.narrative_producer,
                    status=AgentStatus.success,
                    findings={"reason": "bounded repair did not pass", "insight_id": fallback.insight_id},
                    event_ids=fallback.source_event_ids,
                    input_state_version=request.match_state.state_version,
                ))
                return OrchestrationResult(
                    fallback.model_copy(update={"status": InsightStatus.fallback, "agent_findings": findings, "validation": fallback_validation}),
                    fallback_validation,
                    findings,
                    "insight_published",
                    0.0,
                )
        suppressed = repaired_validation.model_copy(update={
            "status": ValidationStatus.suppressed,
            "repair_count": 1,
            "semantic_findings": ["Initial candidate and one repair failed deterministic validation; no insight was published."],
        })
        return OrchestrationResult(None, suppressed, findings, "suppressed", 0.0)
    return OrchestrationResult(
        insight.model_copy(update={"agent_findings": findings, "validation": validation}),
        validation,
        findings,
        "insight_published",
        0.0,
    )


class AgentCoordinator:
    """Synchronous boundary around one short-lived Agent Framework workflow."""

    def run(self, moment: SignificantMoment, match_state: MatchState, evidence: EvidencePackage) -> OrchestrationResult:
        started = time.perf_counter()
        request = OrchestrationRequest(moment=moment, match_state=match_state, evidence=evidence)
        workflow_instance = matchpulse_analysis.build()
        workflow_result = asyncio.run(workflow_instance.run(request))
        result = workflow_result.get_outputs()[0]
        result.duration_ms = (time.perf_counter() - started) * 1000
        return result
