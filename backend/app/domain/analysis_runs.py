"""Inspectable orchestration records; safe operational artifacts, not prompts."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, Field

from app.domain.insights import AgentFinding, ValidationResult


class AnalysisOutcome(str, Enum):
    insight_published = "insight_published"
    suppressed = "suppressed"
    failed = "failed"


class AnalysisRun(BaseModel):
    run_id: str
    match_id: str
    evidence_id: str
    match_state_version: int
    outcome: AnalysisOutcome
    insight_ids: list[str] = Field(default_factory=list)
    stages: list[AgentFinding] = Field(default_factory=list)
    validation: ValidationResult
    duration_ms: float
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
