"""Public HTTP request and response models for API v1."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.domain.events import CanonicalEvent
from app.domain.insights import Insight


class ErrorDetail(BaseModel):
    field: str | None = None
    issue: str


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list[ErrorDetail] = Field(default_factory=list)
    correlation_id: str


class ErrorResponse(BaseModel):
    error: ErrorBody


class IngestEventResponse(BaseModel):
    accepted: bool
    duplicate: bool
    event_id: str
    match_id: str
    processing_status: str
    match_state_version: int
    published_insight_ids: list[str] = Field(default_factory=list)
    analysis_run_ids: list[str] = Field(default_factory=list)
    correlation_id: str


class BatchRequest(BaseModel):
    events: list[CanonicalEvent] = Field(min_length=1, max_length=500)
    processing_mode: str = "inline"


class BatchError(BaseModel):
    event_id: str | None = None
    code: str
    message: str


class BatchResponse(BaseModel):
    match_id: str
    accepted_count: int
    duplicate_count: int
    rejected_count: int
    match_state_version: int
    processing_status: str
    errors: list[BatchError] = Field(default_factory=list)
    published_insight_ids: list[str] = Field(default_factory=list)
    analysis_run_ids: list[str] = Field(default_factory=list)
    correlation_id: str


class InsightsResponse(BaseModel):
    match_id: str
    items: list[Insight]
    next_cursor: str | None = None


class EventsResponse(BaseModel):
    match_id: str
    items: list[CanonicalEvent]
    next_cursor: str | None = None


class FixtureResponse(BaseModel):
    fixture: str
    match_id: str
    accepted_count: int
    published_insight_ids: list[str] = Field(default_factory=list)
    analysis_run_ids: list[str] = Field(default_factory=list)


class StatsBombImportResponse(BaseModel):
    source_match_id: str
    match_id: str
    data_source: str
    historical: bool = True
    live_feed_available: bool = False
    accepted_count: int
    duplicate_count: int = 0
    rejected_count: int = 0
    published_insight_ids: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class StatsBombMatchResponse(BaseModel):
    source_match_id: str
    match_id: str
    home_team: str | None = None
    away_team: str | None = None
    match_date: str | None = None
    competition: str | None = None
    season: str | None = None
    event_count: int


class StatsBombMatchesResponse(BaseModel):
    items: list[StatsBombMatchResponse]
    data_source: str = "statsbomb-open-data"
    live_feed_available: bool = False


class EvidenceResponse(BaseModel):
    evidence_id: str
    insight_id: str
    match_id: str
    match_state_version: int
    window: dict[str, int]
    event_ids: list[str]
    events: list[CanonicalEvent]
    metrics: list[dict[str, Any]]
    validation: dict[str, Any] | None
