# MatchPulse API Specification (Proposed Initial Contract)

## Status and scope

The planning conversation established the need for an event ingestion API, canonical schema, match-state/metrics APIs, orchestration, verified insights, and evidence lookup. It did **not** specify finalized endpoint paths, exact JSON contracts, or authentication. This document proposes a minimal first-pass HTTP API to unblock implementation. These endpoints must be reconciled with the existing repository before coding; do not assume they already exist.

The initial API is intended for controlled development/testing and the first end-to-end product flow. Authentication must be selected before exposing a deployed API publicly. The conversation did not decide on an auth provider or production access model.

## 1. General conventions

- Base path: `/api/v1` (proposed).
- Request/response media type: `application/json` unless explicitly stated otherwise.
- IDs are stable strings. UUID/ULID format is not mandated by the conversation; pick a consistent format and validate it.
- Times should use ISO 8601 UTC timestamps for wall-clock event receipt/creation. Match event position should use explicit match minute/second or a canonical elapsed time. Do not mix wall-clock and match-clock values.
- Use a canonical event contract across providers. Source adapters perform source-specific mapping.
- Errors should return a predictable structure containing a machine-readable code, human-readable message, and optional field details/correlation ID.
- All insight runs must refer to an immutable/versioned match-state or evidence-window snapshot.
- API results must distinguish “no insight detected” from “processing failed.”
- Never accept arbitrary model prose as a verified insight without validation and audit metadata.

## 2. Canonical event object (proposed)

Example shape, based on fields discussed in the conversation. Exact enums, coordinate bounds, and optionality must be formalized in code.

```json
{
  "event_id": "evt_00721",
  "match_id": "sim_match_001",
  "minute": 72,
  "second": 14,
  "event_type": "high_regain",
  "team_id": "ridge_united",
  "player_id": "player_08",
  "x": 76.4,
  "y": 39.2,
  "zone": "attacking_third",
  "timestamp": "2026-10-22T10:15:00Z",
  "source": {
    "adapter": "manual-or-test",
    "source_event_id": "evt_00721"
  },
  "attributes": {}
}
```

Field guidance:

| Field | Expected behavior |
|---|---|
| `event_id` | Stable unique ID within the agreed domain; duplicate behavior must be deterministic. |
| `match_id` | Required match identifier. |
| `minute`, `second` | Match-clock position; validate allowed ranges and document period/extra-time conventions. |
| `event_type` | Controlled canonical event taxonomy. At minimum support event families required by implemented features, such as pass, shot, tackle, possession change, high regain, penalty-box entry, and pressure-related events when available. |
| `team_id` | Team associated with the event where applicable. |
| `player_id` | Optional only for event types for which player identity is genuinely unavailable; do not invent a player. |
| `x`, `y` | Optional spatial position(s) according to the event type and source. Document coordinate system/dimensions. |
| `zone` | Optional normalized zone if available or deterministically computed from coordinates. |
| `timestamp` | Optional source/wall-clock timestamp, distinct from match clock. Decide whether it is required for source synchronization. |
| `source` | Provenance/adapter identity; must not redefine canonical fields. |
| `attributes` | Typed event-type-specific fields, validated per type. Prefer explicit typed fields for data used by analytics. |

A real source may require extra details such as pass origin/target coordinates, outcome, body part, pressure, phase/period, or ball-speed information. Add fields based on evidence from the selected source; do not make all possible football fields mandatory for every event.

## 3. Proposed endpoints

### 3.1 Health check

`GET /api/v1/health`

Purpose: readiness/liveness for local operation and deployment checks.

Proposed response:

```json
{
  "status": "ok",
  "service": "matchpulse-api",
  "version": "0.1.0"
}
```

The service should not leak secrets or internal configuration details from this endpoint.

### 3.2 Ingest one event

`POST /api/v1/matches/{match_id}/events`

Purpose: validate and accept one canonical event.

Request body: one canonical event object. The path `match_id` must match the body `match_id`; otherwise return a validation error.

Proposed response for a newly accepted event:

```json
{
  "accepted": true,
  "duplicate": false,
  "event_id": "evt_00721",
  "match_id": "sim_match_001",
  "processing_status": "processed",
  "match_state_version": 18,
  "correlation_id": "corr_example"
}
```

Possible `processing_status` values to define and keep stable include `accepted`, `processing`, `processed`, and `failed`. If processing is asynchronous later, return `accepted`/`processing` and expose a status endpoint. If implemented synchronously, `processed` means state/metrics have been updated; it does not automatically mean an insight was generated.

Duplicate behavior must be explicit. Recommended initial behavior: recognize an identical `event_id` as a duplicate and avoid applying it twice; return a duplicate marker or a conflict if the body differs from the stored event. Decide and test the exact HTTP status behavior.

### 3.3 Ingest a batch of events

`POST /api/v1/matches/{match_id}/events:batch`

This route is proposed and optional for the first increment. It is useful for test fixtures and source adapters that naturally deliver batches. An alternative REST-style route such as `POST /api/v1/matches/{match_id}/events/batch` is equally reasonable; choose one convention and use it consistently.

Proposed request:

```json
{
  "events": [
    {
      "event_id": "evt_00721",
      "match_id": "sim_match_001",
      "minute": 72,
      "second": 14,
      "event_type": "high_regain",
      "team_id": "ridge_united",
      "player_id": "player_08",
      "x": 76.4,
      "y": 39.2,
      "zone": "attacking_third"
    }
  ],
  "processing_mode": "inline"
}
```

Proposed response:

```json
{
  "match_id": "sim_match_001",
  "accepted_count": 1,
  "duplicate_count": 0,
  "rejected_count": 0,
  "match_state_version": 18,
  "processing_status": "processed",
  "errors": [],
  "correlation_id": "corr_example"
}
```

Choose and document all-or-nothing versus partial batch acceptance. For an evaluation-friendly initial implementation, either fail the batch atomically with field errors or return explicit per-event outcomes; never drop bad events silently.

### 3.4 Read match state

`GET /api/v1/matches/{match_id}/state`

Purpose: return the latest deterministic match state and calculated metrics.

Proposed response:

```json
{
  "match_id": "sim_match_001",
  "state_version": 18,
  "match_clock": {
    "minute": 72,
    "second": 14
  },
  "teams": [],
  "metrics": {
    "pressure_index": {
      "team_id": "ridge_united",
      "value": 72,
      "previous_window_value": 31,
      "delta": 41,
      "window_seconds": 300,
      "previous_window_seconds": 300,
      "definition_version": "pressure-v1"
    }
  },
  "updated_at": "2026-10-22T10:15:00Z"
}
```

This example is illustrative only. The values are not official football metrics or live match statistics. Do not hardcode this example's values. The actual response should include the available metrics supported by the processed data, and identify missing/undefined values explicitly.

### 3.5 List insights for a match

`GET /api/v1/matches/{match_id}/insights?limit=20&after=...`

Purpose: list verified insights, ordered by event/match time or another documented stable ordering.

Proposed response:

```json
{
  "match_id": "sim_match_001",
  "items": [
    {
      "insight_id": "insight_0001",
      "version": 1,
      "status": "verified",
      "match_clock": { "minute": 72, "second": 14 },
      "headline": "Pressure swing detected",
      "summary": "Ridge United have increased their attacking pressure.",
      "why_it_matters": "The recent event sequence suggests Harbor FC is facing more pressure when progressing the ball.",
      "audience_variants": {
        "fan": {},
        "analyst": {},
        "broadcast": {}
      },
      "evidence_id": "evidence_0001",
      "created_at": "2026-10-22T10:15:00Z"
    }
  ],
  "next_cursor": null
}
```

Do not expose an unverified candidate as a published verified insight. Candidate/failed runs can be exposed separately for developer diagnostics if access-controlled.

### 3.6 Get one insight and its evidence

`GET /api/v1/insights/{insight_id}`

Purpose: return the published story and evidence references.

`GET /api/v1/insights/{insight_id}/evidence`

Purpose: return supporting events/metrics and validation metadata for the Show Evidence UI.

Proposed evidence response:

```json
{
  "evidence_id": "evidence_0001",
  "insight_id": "insight_0001",
  "match_id": "sim_match_001",
  "match_state_version": 18,
  "window": {
    "start_minute": 67,
    "start_second": 14,
    "end_minute": 72,
    "end_second": 14
  },
  "event_ids": ["evt_00721"],
  "metrics": {
    "pressure_index_before": 31,
    "pressure_index_after": 72,
    "delta": 41,
    "definition_version": "pressure-v1"
  },
  "agent_runs": [],
  "validation": {
    "status": "approved",
    "checks": [],
    "repair_count": 0
  }
}
```

The actual event window must be derived from the saved evidence snapshot. The example should not dictate the production window logic if the actual metric uses another interval.

### 3.7 Request an analysis run (optional if ingestion triggers it)

`POST /api/v1/matches/{match_id}/analysis-runs`

Purpose: explicitly request analysis for a match-state version or candidate time window, useful for replay, evaluation, or controlled manual review. This may be unnecessary if new events automatically trigger detection and orchestration.

Proposed request:

```json
{
  "state_version": 18,
  "audiences": ["fan", "analyst", "broadcast"],
  "preferences": {
    "favorite_team_id": "ridge_united",
    "favorite_player_id": null,
    "language": "en"
  },
  "reason": "manual_replay"
}
```

Proposed response:

```json
{
  "run_id": "run_0001",
  "match_id": "sim_match_001",
  "state_version": 18,
  "status": "completed",
  "outcome": "insight_published",
  "insight_ids": ["insight_0001"],
  "correlation_id": "corr_example"
}
```

Possible outcome values include `insight_published`, `no_significant_moment`, `rejected`, `fallback_published`, and `failed`. Final enum names should be fixed in schemas and used in the UI consistently.

### 3.8 Read agent-run status and artifacts (developer/evaluator feature)

`GET /api/v1/analysis-runs/{run_id}`

`GET /api/v1/analysis-runs/{run_id}/trace`

Purpose: expose structured agent stages, timings, handoffs, validation results, retries, and safe diagnostics. Do not expose secrets, hidden chain-of-thought, or unfiltered internal prompts. Expose operational artifacts such as typed agent outputs, summarized findings, tool/event references, statuses, and errors.

Proposed trace response:

```json
{
  "run_id": "run_0001",
  "status": "completed",
  "stages": [
    {
      "stage": "match_analyst",
      "status": "completed",
      "input_state_version": 18,
      "output_schema_version": "match-analysis-v1",
      "duration_ms": 420,
      "event_ids": ["evt_00721"]
    },
    {
      "stage": "evidence_auditor",
      "status": "approved",
      "repair_count": 0,
      "duration_ms": 110
    }
  ],
  "correlation_id": "corr_example"
}
```

Durations are sample values only and must be measured in the application.

## 4. Proposed shared response/error shape

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The event payload is invalid.",
    "details": [
      {
        "field": "event_type",
        "issue": "Unsupported canonical event type."
      }
    ],
    "correlation_id": "corr_example"
  }
}
```

Use appropriate HTTP status codes consistently. Candidate mapping:
- `400` for malformed request JSON or an invalid query/path parameter.
- `401` / `403` when authentication/authorization is implemented.
- `404` for a missing match/insight/run.
- `409` for a conflicting duplicate event ID if that behavior is chosen.
- `422` for structurally valid JSON that fails schema/business validation.
- `429` for rate limits if applicable.
- `500` for unexpected server failures without exposing stack traces.
- `503` for unavailable dependencies or service-not-ready conditions.

Finalize exact mapping in the API implementation and tests; this list is guidance, not a claim about existing behavior.

## 5. Authentication and authorization

The conversation did not establish an auth approach. Do not invent one as a settled decision.

Implementation guidance:
- Local development can use an explicitly local-only configuration, but it must not accidentally disable authentication on a public deployment.
- Before public deployment, decide whether the frontend is the only allowed caller, whether users need individual accounts, and whether developer/trace APIs require restricted access.
- If deployed to Azure, evaluate the available platform identity/authentication options appropriate to the architecture. Keep identity checks out of business logic where practical.
- Never place API keys or database credentials in frontend code or commit them to source control.

## 6. Versioning and compatibility

- Version canonical event schema and any source adapter mapping that changes normalized meaning.
- Version metric definitions/threshold configurations; an evidence record must identify which version was used.
- Version agent I/O schemas and broadcast payloads.
- A stored insight must remain interpretable if formulas or prompts change later.
- Treat the API path version and the metric/story schema version as separate concepts.

## 7. Out of scope for the initial API

Unless later requirements justify them, do not make the initial implementation depend on:
- WebSockets or server-sent events;
- Event Hubs or an asynchronous broker;
- a full match simulator endpoint;
- automatic video event extraction;
- an external live-match provider;
- complex multi-tenant account management.

The first goal is a reliable, testable HTTP event-to-verified-insight path. Streaming and provider-specific features can be added behind the source-independent contracts later.
