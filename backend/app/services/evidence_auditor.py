"""Deterministic validation of the first vertical slice's evidence packages."""

from __future__ import annotations

from app.analytics.evidence_builder import EvidencePackage
from app.domain.insights import Insight, ValidationCheck, ValidationResult, ValidationStatus
from app.domain.match_state import MatchState


class EvidenceAuditor:
    """Checks references and snapshot consistency without relying on an LLM."""

    def validate(
        self, evidence: EvidencePackage, match_state: MatchState, insight: Insight | None = None,
    ) -> ValidationResult:
        window = evidence.evidence_window
        start = window.start_minute * 60 + window.start_second
        end = window.end_minute * 60 + window.end_second
        event_ids = [event.event_id for event in evidence.events_in_window]
        checks = [
            ValidationCheck(
                check_type="state_version",
                field="match_state_version",
                expected=match_state.state_version,
                actual=evidence.match_state_version,
                passed=evidence.match_state_version == match_state.state_version,
                message="Evidence was built from the current immutable state version.",
            ),
            ValidationCheck(
                check_type="event_window",
                field="source_event_ids",
                expected="all events belong to the declared match-time window",
                actual=event_ids,
                passed=all(start <= event.clock_seconds <= end for event in evidence.events_in_window),
                message="Each supporting event is inside the declared evidence window.",
            ),
            ValidationCheck(
                check_type="trigger_reference",
                field="trigger_event_id",
                expected=evidence.moment.trigger_event_id,
                actual=event_ids,
                passed=evidence.moment.trigger_event_id in event_ids,
                message="The detected trigger is included in its evidence package.",
            ),
            ValidationCheck(
                check_type="event_ledger",
                field="event_ids",
                expected="unique, processed event IDs",
                actual=event_ids,
                passed=len(event_ids) == len(set(event_ids)) and all(event_id in match_state.events for event_id in event_ids),
                message="Evidence references resolve to the processed match ledger.",
            ),
        ]
        if insight is not None:
            checks.extend([
                ValidationCheck(
                    check_type="insight_match",
                    field="match_id",
                    expected=match_state.match_id,
                    actual=insight.match_id,
                    passed=insight.match_id == match_state.match_id,
                    message="The proposed insight belongs to the evidence match.",
                ),
                ValidationCheck(
                    check_type="insight_references",
                    field="source_event_ids",
                    expected=event_ids,
                    actual=insight.source_event_ids,
                    passed=insight.source_event_ids == event_ids,
                    message="The insight cites exactly the validated evidence events.",
                ),
                ValidationCheck(
                    check_type="insight_evidence",
                    field="evidence_id",
                    expected=evidence.evidence_id,
                    actual=insight.evidence_id,
                    passed=insight.evidence_id == evidence.evidence_id,
                    message="The insight references the immutable evidence package.",
                ),
            ])
        approved = all(check.passed for check in checks)
        return ValidationResult(
            status=ValidationStatus.approved if approved else ValidationStatus.rejected,
            checks=checks,
            semantic_findings=[] if approved else ["Deterministic evidence validation failed; insight was not published."],
        )
