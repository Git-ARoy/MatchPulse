"""Insight and evidence models for MatchPulse.

Insights are the primary deliverable of the platform: evidence-linked,
audience-adapted narratives describing significant match moments.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------

class EvidenceWindow(BaseModel):
    """Time-bounded window of events that support an insight."""

    start_minute: int
    start_second: int
    end_minute: int
    end_second: int
    event_ids: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

class MetricSnapshot(BaseModel):
    """Point-in-time metric value with optional delta."""

    name: str
    value: float
    previous_value: float | None = None
    delta: float | None = None
    definition_version: str = "pressure-v1"
    team_id: str | None = None


# ---------------------------------------------------------------------------
# Agent trace artefacts
# ---------------------------------------------------------------------------

class AgentStage(str, Enum):
    match_analyst = "match_analyst"
    tactical_analyst = "tactical_analyst"
    narrative_producer = "narrative_producer"
    evidence_auditor = "evidence_auditor"


class AgentStatus(str, Enum):
    success = "success"
    failure = "failure"
    skipped = "skipped"


class AgentFinding(BaseModel):
    """Record of a single agent's contribution to the insight pipeline."""

    agent_name: str
    stage: AgentStage
    status: AgentStatus
    findings: dict[str, Any] = Field(default_factory=dict)
    duration_ms: float = 0.0
    event_ids: list[str] = Field(default_factory=list)
    input_state_version: int = 0


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

class ValidationStatus(str, Enum):
    approved = "approved"
    rejected = "rejected"
    repaired = "repaired"
    fallback = "fallback"
    suppressed = "suppressed"


class ValidationCheck(BaseModel):
    """Single deterministic check applied during evidence audit."""

    check_type: str
    field: str
    expected: Any = None
    actual: Any = None
    passed: bool = True
    message: str = ""


class ValidationResult(BaseModel):
    """Aggregate validation outcome for an insight."""

    status: ValidationStatus
    checks: list[ValidationCheck] = Field(default_factory=list)
    repair_count: int = 0
    semantic_findings: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Audience variants
# ---------------------------------------------------------------------------

class AudienceMode(str, Enum):
    fan = "fan"
    analyst = "analyst"
    broadcast = "broadcast"


class AudienceVariant(BaseModel):
    """Audience-specific rendering of the same underlying insight."""

    mode: AudienceMode
    headline: str
    summary: str
    why_it_matters: str
    detail: str | None = None
    next_watch: str | None = None


# ---------------------------------------------------------------------------
# Top-level Insight
# ---------------------------------------------------------------------------

class InsightStatus(str, Enum):
    verified = "verified"
    rejected = "rejected"
    fallback = "fallback"
    suppressed = "suppressed"


class InsightType(str, Enum):
    pressure_shift = "pressure_shift"
    goal = "goal"
    red_card = "red_card"
    shot_burst = "shot_burst"
    possession_swing = "possession_swing"


class Insight(BaseModel):
    """Fully verified, audience-adapted insight about a significant match moment."""

    insight_id: str
    evidence_id: str
    version: int = 1
    match_id: str
    match_state_version: int
    match_clock: dict[str, int] = Field(default_factory=dict, description="{'minute': m, 'second': s}")
    insight_type: InsightType
    headline: str
    summary: str
    what_changed: str
    why_it_matters: str
    evidence: EvidenceWindow
    metrics: list[MetricSnapshot] = Field(default_factory=list)
    source_event_ids: list[str] = Field(default_factory=list)
    agent_findings: list[AgentFinding] = Field(default_factory=list)
    validation: ValidationResult | None = None
    audience_variants: dict[str, AudienceVariant] = Field(default_factory=dict)
    status: InsightStatus = InsightStatus.verified
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
