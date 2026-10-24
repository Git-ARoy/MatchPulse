"""Typed contracts shared by MatchPulse's specialist analysis roles.

These contracts separate the immutable deterministic evidence snapshot from
each agent's interpretation. A future Foundry-backed implementation must use
the same contracts and cannot alter calculated facts.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.domain.insights import AgentFinding, MetricSnapshot


class EvidenceContext(BaseModel):
    """Minimal immutable fact set handed to every role in one analysis run."""

    model_config = ConfigDict(frozen=True)

    match_id: str
    match_state_version: int
    moment_type: str
    trigger_event_id: str
    match_clock: dict[str, int]
    evidence_id: str
    event_ids: tuple[str, ...]
    event_types: tuple[str, ...]
    zones: tuple[str, ...]
    metrics: tuple[MetricSnapshot, ...]
    team_state: dict[str, dict[str, int]]


class MatchAnalysisOutput(BaseModel):
    finding: AgentFinding


class TacticalAnalysisOutput(BaseModel):
    finding: AgentFinding


class NarrativeOutput(BaseModel):
    headline: str
    summary: str
    what_changed: str
    why_it_matters: str


class AuditOutput(BaseModel):
    approved: bool
    checks: list[dict[str, Any]] = Field(default_factory=list)
