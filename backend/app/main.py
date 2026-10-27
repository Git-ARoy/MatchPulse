"""FastAPI entry point for MatchPulse's deterministic first vertical slice."""

from __future__ import annotations

import asyncio
import os
import uuid
from typing import Any

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.domain.events import CanonicalEvent
from app.adapters.statsbomb_open_data import StatsBombDataError, StatsBombOpenDataAdapter
from app.dev.fixtures import FIXTURE_NAMES, build_fixture
from app.dev.synthetic_scenarios import build_scenario, list_scenarios
from app.schemas.api import (
    BatchError,
    BatchRequest,
    BatchResponse,
    ErrorResponse,
    EvidenceResponse,
    EventsResponse,
    FixtureResponse,
    IngestEventResponse,
    InsightsResponse,
    MatchRecapResponse,
    StatsBombMatchesResponse,
    StatsBombMatchResponse,
    StatsBombImportResponse,
    SyntheticScenarioListResponse,
    SyntheticScenarioResponse,
    SyntheticScenarioSummary,
)
from app.services.match_service import (
    EventConflictError,
    EventOrderError,
    InsightNotFoundError,
    MatchNotFoundError,
    MatchService,
)
from app.services.live_bus import live_bus

app = FastAPI(title="MatchPulse API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

service = MatchService()


@app.middleware("http")
async def edge_cache_headers(request: Request, call_next):
    response = await call_next(request)
    if request.method == "GET" and request.url.path.startswith("/api/v1/"):
        response.headers["Cache-Control"] = "public, s-maxage=1, stale-while-revalidate=2"
    return response


def correlation_id(request: Request) -> str:
    return request.headers.get("X-Correlation-ID", f"corr_{uuid.uuid4().hex}")


def error_response(
    request: Request, status_code: int, code: str, message: str, details: list[dict[str, Any]] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(error={
            "code": code,
            "message": message,
            "details": details or [],
            "correlation_id": correlation_id(request),
        }).model_dump(mode="json"),
    )


@app.exception_handler(RequestValidationError)
async def request_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    details = [
        {"field": ".".join(str(part) for part in error["loc"] if part != "body"), "issue": error["msg"]}
        for error in exc.errors()
    ]
    return error_response(request, status.HTTP_422_UNPROCESSABLE_CONTENT, "VALIDATION_ERROR", "The request payload is invalid.", details)


@app.get("/api/v1/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "matchpulse-api", "version": "0.1.0"}


@app.get("/api/v1/health/liveness")
def liveness() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/health/readiness")
def readiness() -> dict[str, str]:
    return {"status": "ready"}


@app.get("/api/v1/demo/scenarios", response_model=SyntheticScenarioListResponse)
def list_synthetic_scenarios() -> SyntheticScenarioListResponse:
    """Return the fictional, football-realistic sequences used by the demo."""
    return SyntheticScenarioListResponse(items=[SyntheticScenarioSummary(**item.__dict__) for item in list_scenarios()])


@app.post("/api/v1/demo/scenarios/{scenario_id}", response_model=SyntheticScenarioResponse, responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}})
async def load_synthetic_scenario(scenario_id: str, request: Request) -> SyntheticScenarioResponse | JSONResponse:
    """Ingest a safe synthetic showcase scenario through the production pipeline."""
    scenario_lookup = {item.scenario_id: item for item in list_scenarios()}
    scenario = scenario_lookup.get(scenario_id)
    if scenario is None:
        return error_response(request, 404, "SCENARIO_NOT_FOUND", "Unknown synthetic scenario.")
    if service.has_events(scenario.match_id):
        return error_response(request, 409, "SCENARIO_ALREADY_LOADED", "This synthetic scenario is already loaded in the current process.")
    published_ids: list[str] = []
    run_ids: list[str] = []
    try:
        events = build_scenario(scenario_id)
        for event in events:
            outcome = await asyncio.to_thread(service.ingest, event)
            await publish_ingestion(event.match_id, event, outcome)
            published_ids.extend(item.insight_id for item in outcome.published_insights)
            run_ids.extend(outcome.analysis_run_ids)
    except (EventConflictError, EventOrderError) as error:
        return error_response(request, 409, "SCENARIO_INGESTION_FAILED", str(error))
    return SyntheticScenarioResponse(
        fixture=scenario_id,
        match_id=scenario.match_id,
        accepted_count=len(events),
        published_insight_ids=published_ids,
        analysis_run_ids=run_ids,
    )


@app.post("/api/v1/import/statsbomb/{source_match_id}", response_model=StatsBombImportResponse)
async def import_statsbomb_match(source_match_id: str, request: Request) -> StatsBombImportResponse | JSONResponse:
    """Import one completed Hudl/StatsBomb Open Data match into the ledger.

    ``STATSBOMB_OPEN_DATA_ROOT`` must point at a checked-out copy of the
    repository. The endpoint never treats these historical events as live.
    """
    try:
        summary, events = await asyncio.to_thread(StatsBombOpenDataAdapter().load_match, source_match_id)
    except StatsBombDataError as error:
        return error_response(request, 422, "STATSBOMB_IMPORT_ERROR", str(error))
    match_id = summary.match_id if summary else f"statsbomb_{source_match_id}"
    accepted = duplicates = rejected = 0
    insight_ids: list[str] = []
    errors: list[str] = []
    for event in events:
        try:
            outcome = await asyncio.to_thread(service.ingest, event)
            accepted += int(outcome.accepted)
            duplicates += int(outcome.duplicate)
            insight_ids.extend(item.insight_id for item in outcome.published_insights)
        except (EventConflictError, EventOrderError) as error:
            rejected += 1
            errors.append(f"{event.event_id}: {error}")
    return StatsBombImportResponse(
        source_match_id=source_match_id,
        match_id=match_id,
        data_source="statsbomb-open-data",
        accepted_count=accepted,
        duplicate_count=duplicates,
        rejected_count=rejected,
        published_insight_ids=insight_ids,
        errors=errors[:20],
    )


@app.get("/api/v1/import/statsbomb/matches", response_model=StatsBombMatchesResponse)
def list_statsbomb_matches(
    request: Request,
    competition_id: int | None = None,
    season_id: int | None = None,
    limit: int = 100,
) -> StatsBombMatchesResponse | JSONResponse:
    """List completed Open Data matches available for import.

    This is deliberately a read-only discovery endpoint. Open Data contains
    historical matches, so every item is explicitly marked as non-live.
    """
    try:
        matches = StatsBombOpenDataAdapter().list_available_matches(competition_id, season_id, limit)
    except StatsBombDataError as error:
        return error_response(request, 422, "STATSBOMB_IMPORT_ERROR", str(error))
    return StatsBombMatchesResponse(items=[StatsBombMatchResponse(**match.__dict__) for match in matches])


async def publish_ingestion(match_id: str, event: CanonicalEvent, outcome: object) -> None:
    """Publish a single ordered transition after the write has committed."""
    from app.services.match_service import IngestionOutcome
    result = outcome if isinstance(outcome, IngestionOutcome) else None
    await live_bus.publish(match_id, {
        "type": "match.transition",
        "event": event.model_dump(mode="json"),
        "state": service.get_state_view(match_id),
        "insights": [insight.model_dump(mode="json") for insight in (result.published_insights if result else [])],
    })


@app.post("/api/v1/matches/{match_id}/events", response_model=IngestEventResponse, responses={422: {"model": ErrorResponse}, 409: {"model": ErrorResponse}})
async def ingest_event(match_id: str, event: CanonicalEvent, request: Request) -> IngestEventResponse | JSONResponse:
    if match_id != event.match_id:
        return error_response(request, 422, "MATCH_ID_MISMATCH", "Path match_id must match body match_id.", [{"field": "match_id", "issue": "does not match the path parameter"}])
    try:
        outcome = await asyncio.to_thread(service.ingest, event)
    except EventConflictError as error:
        return error_response(request, 409, "EVENT_CONFLICT", str(error))
    except EventOrderError as error:
        return error_response(request, 409, "EVENT_OUT_OF_ORDER", str(error))
    if outcome.accepted:
        await publish_ingestion(match_id, event, outcome)
    return IngestEventResponse(
        accepted=outcome.accepted,
        duplicate=outcome.duplicate,
        event_id=event.event_id,
        match_id=match_id,
        processing_status="processed",
        match_state_version=outcome.state_version,
        published_insight_ids=[item.insight_id for item in outcome.published_insights],
        analysis_run_ids=outcome.analysis_run_ids,
        correlation_id=correlation_id(request),
    )


@app.post("/api/v1/matches/{match_id}/events:batch", response_model=BatchResponse, responses={422: {"model": ErrorResponse}})
async def ingest_batch(match_id: str, body: BatchRequest, request: Request) -> BatchResponse | JSONResponse:
    if body.processing_mode != "inline":
        return error_response(request, 422, "UNSUPPORTED_PROCESSING_MODE", "Only inline processing is available in the first increment.", [{"field": "processing_mode", "issue": "must be 'inline'"}])
    accepted = duplicates = rejected = 0
    errors: list[BatchError] = []
    published_ids: list[str] = []
    run_ids: list[str] = []
    state_version = 0
    for event in body.events:
        if event.match_id != match_id:
            rejected += 1
            errors.append(BatchError(event_id=event.event_id, code="MATCH_ID_MISMATCH", message="Body match_id does not match the path parameter."))
            continue
        try:
            outcome = await asyncio.to_thread(service.ingest, event)
            if outcome.accepted:
                await publish_ingestion(match_id, event, outcome)
            accepted += int(outcome.accepted)
            duplicates += int(outcome.duplicate)
            state_version = outcome.state_version
            published_ids.extend(item.insight_id for item in outcome.published_insights)
            run_ids.extend(outcome.analysis_run_ids)
        except (EventConflictError, EventOrderError) as error:
            rejected += 1
            errors.append(BatchError(event_id=event.event_id, code="EVENT_CONFLICT" if isinstance(error, EventConflictError) else "EVENT_OUT_OF_ORDER", message=str(error)))
    if state_version == 0:
        try:
            state_version = service.get_state(match_id).state_version
        except MatchNotFoundError:
            pass
    return BatchResponse(
        match_id=match_id,
        accepted_count=accepted,
        duplicate_count=duplicates,
        rejected_count=rejected,
        match_state_version=state_version,
        processing_status="processed",
        errors=errors,
        published_insight_ids=published_ids,
        analysis_run_ids=run_ids,
        correlation_id=correlation_id(request),
    )


@app.get("/api/v1/matches")
def list_active_matches() -> dict[str, Any]:
    """Discover all active matches currently registered in the ledger."""
    return {"items": service.list_matches()}


@app.get("/api/v1/matches/{match_id}/state", response_model=None, responses={404: {"model": ErrorResponse}})
def get_state(match_id: str, request: Request) -> dict[str, Any] | JSONResponse:
    try:
        match_state = service.get_state_view(match_id)
    except MatchNotFoundError as error:
        return error_response(request, 404, "MATCH_NOT_FOUND", str(error))
    return match_state


@app.get("/api/v1/matches/{match_id}/tracking", response_model=None, responses={404: {"model": ErrorResponse}})
async def get_match_tracking(match_id: str, request: Request) -> dict[str, Any] | JSONResponse:
    """Fetch live 22-player and ball tracking telemetry from the simulation engine."""
    import httpx
    sim_url = os.getenv("SIMULATOR_API_URL", "http://localhost:8050").rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=1.5) as client:
            res = await client.get(f"{sim_url}/api/simulation/tracking")
            if res.status_code == 200:
                data = res.json()
                if data.get("match_id") == match_id:
                    return data
    except Exception:
        pass
    return error_response(request, 404, "TRACKING_UNAVAILABLE", "No live simulation tracking source connected for this match.")


@app.get("/api/v1/matches/{match_id}/events", response_model=EventsResponse, responses={404: {"model": ErrorResponse}})
def list_events(match_id: str, request: Request, limit: int = 50, after: str | None = None) -> EventsResponse | JSONResponse:
    """Read the accepted canonical ledger for the live event ticker."""
    if not 1 <= limit <= 100:
        return error_response(request, 422, "INVALID_LIMIT", "limit must be between 1 and 100.")
    try:
        items, next_cursor = service.list_events(match_id, limit, after)
    except (MatchNotFoundError, InsightNotFoundError) as error:
        return error_response(request, 404, "NOT_FOUND", str(error))
    return EventsResponse(match_id=match_id, items=items, next_cursor=next_cursor)


@app.post("/api/v1/dev/matches/{match_id}/fixtures/{fixture_name}", response_model=FixtureResponse, responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}})
async def inject_development_fixture(match_id: str, fixture_name: str, request: Request) -> FixtureResponse | JSONResponse:
    """Inject one small synthetic sequence into a previously empty local match.

    This endpoint is intentionally namespaced under ``/dev`` and is not a
    production ingestion path. It exists solely to exercise the real API from
    the development console without embedding client-side fake events.
    """
    if fixture_name not in FIXTURE_NAMES:
        return error_response(request, 404, "FIXTURE_NOT_FOUND", "Unknown synthetic fixture.", [{"field": "fixture_name", "issue": f"must be one of {', '.join(FIXTURE_NAMES)}"}])
    if service.has_events(match_id):
        return error_response(request, 409, "FIXTURE_REQUIRES_EMPTY_MATCH", "Synthetic fixtures may only be loaded into an empty match ID.")
    published_ids: list[str] = []
    run_ids: list[str] = []
    try:
        for event in build_fixture(fixture_name, match_id):
            outcome = await asyncio.to_thread(service.ingest, event)
            await publish_ingestion(match_id, event, outcome)
            published_ids.extend(item.insight_id for item in outcome.published_insights)
            run_ids.extend(outcome.analysis_run_ids)
    except (EventConflictError, EventOrderError) as error:  # defensive: fixtures are chronological and unique
        return error_response(request, 409, "FIXTURE_INGESTION_FAILED", str(error))
    return FixtureResponse(
        fixture=fixture_name,
        match_id=match_id,
        accepted_count=len(build_fixture(fixture_name, match_id)),
        published_insight_ids=published_ids,
        analysis_run_ids=run_ids,
    )


@app.websocket("/api/v1/matches/{match_id}/live-stream")
async def live_stream(match_id: str, websocket: WebSocket) -> None:
    """Push event ticker items, state snapshots, and verified insights."""
    await websocket.accept()
    queue = live_bus.subscribe(match_id)
    try:
        try:
            await websocket.send_json({"type": "match.snapshot", "state": service.get_state_view(match_id)})
        except MatchNotFoundError:
            await websocket.send_json({"type": "match.awaiting_events", "match_id": match_id})
        while True:
            message = await queue.get()
            await websocket.send_json(message)
    except WebSocketDisconnect:
        pass
    finally:
        live_bus.unsubscribe(match_id, queue)


@app.get("/api/v1/matches/{match_id}/insights", response_model=InsightsResponse, responses={404: {"model": ErrorResponse}})
def list_insights(match_id: str, request: Request, limit: int = 20, after: str | None = None) -> InsightsResponse | JSONResponse:
    if not 1 <= limit <= 100:
        return error_response(request, 422, "INVALID_LIMIT", "limit must be between 1 and 100.")
    try:
        items, next_cursor = service.list_insights(match_id, limit, after)
    except (MatchNotFoundError, InsightNotFoundError) as error:
        return error_response(request, 404, "NOT_FOUND", str(error))
    return InsightsResponse(match_id=match_id, items=items, next_cursor=next_cursor)


@app.get("/api/v1/matches/{match_id}/recap", response_model=MatchRecapResponse, responses={404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}})
def get_match_recap(match_id: str, request: Request, audience: str = "fan", language: str = "en") -> MatchRecapResponse | JSONResponse:
    """Render a verified, audience-specific recap with no ungrounded claims."""
    try:
        return MatchRecapResponse(**service.build_recap(match_id, audience, language))
    except MatchNotFoundError as error:
        return error_response(request, 404, "MATCH_NOT_FOUND", str(error))
    except ValueError as error:
        return error_response(request, 422, "INVALID_RECAP_PREFERENCE", str(error))


@app.get("/api/v1/insights/{insight_id}", responses={404: {"model": ErrorResponse}})
def get_insight(insight_id: str, request: Request):
    try:
        return service.get_insight(insight_id)
    except InsightNotFoundError as error:
        return error_response(request, 404, "INSIGHT_NOT_FOUND", str(error))


@app.get("/api/v1/insights/{insight_id}/evidence", response_model=EvidenceResponse, responses={404: {"model": ErrorResponse}})
def get_evidence(insight_id: str, request: Request) -> EvidenceResponse | JSONResponse:
    try:
        insight = service.get_insight(insight_id)
        evidence = service.get_evidence(insight_id)
    except InsightNotFoundError as error:
        return error_response(request, 404, "INSIGHT_NOT_FOUND", str(error))
    window = evidence.evidence_window
    return EvidenceResponse(
        evidence_id=evidence.evidence_id,
        insight_id=insight.insight_id,
        match_id=insight.match_id,
        match_state_version=evidence.match_state_version,
        window={
            "start_minute": window.start_minute,
            "start_second": window.start_second,
            "end_minute": window.end_minute,
            "end_second": window.end_second,
        },
        event_ids=window.event_ids,
        events=evidence.events_in_window,
        metrics=[metric.model_dump() for metric in evidence.metrics],
        validation=insight.validation.model_dump() if insight.validation else None,
    )


@app.get("/api/v1/analysis-runs/{run_id}", responses={404: {"model": ErrorResponse}})
def get_analysis_run(run_id: str, request: Request):
    try:
        return service.get_analysis_run(run_id)
    except InsightNotFoundError as error:
        return error_response(request, 404, "ANALYSIS_RUN_NOT_FOUND", str(error))


@app.get("/api/v1/analysis-runs/{run_id}/trace", responses={404: {"model": ErrorResponse}})
def get_analysis_trace(run_id: str, request: Request):
    """Expose bounded typed findings and timings, never hidden prompts or secrets."""
    try:
        run = service.get_analysis_run(run_id)
    except InsightNotFoundError as error:
        return error_response(request, 404, "ANALYSIS_RUN_NOT_FOUND", str(error))
    return {
        "run_id": run.run_id,
        "status": "completed" if run.outcome.value != "failed" else "failed",
        "outcome": run.outcome.value,
        "match_id": run.match_id,
        "match_state_version": run.match_state_version,
        "evidence_id": run.evidence_id,
        "duration_ms": run.duration_ms,
        "stages": [stage.model_dump(mode="json") for stage in run.stages],
        "validation": run.validation.model_dump(mode="json"),
    }
