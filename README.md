# MatchPulse

MatchPulse is an evidence-first football intelligence platform for synthetic,
football-realistic events. This repository currently contains the first
working backend vertical slice: canonical event ingestion, deterministic match
state and pressure detection, evidence validation, and API retrieval of a
verified insight. It does not use a provider feed, real Premier League data,
or an LLM for statistics.

## What is implemented

- Source-independent `event-v1` canonical event validation with normalized
  0--100 coordinates, provenance metadata, and event-specific attributes.
- Inline, in-memory event ledger with exact-duplicate idempotency and explicit
  rejection of conflicting duplicate IDs and out-of-order match-clock events.
- Deterministic match state, five-minute rolling windows, significant-moment
  detection, immutable evidence packages, and reference validation.
- A Microsoft Agent Framework workflow with concurrent, typed Match Analyst
  and Tactical Analyst stages followed by Narrative Producer and Evidence
  Auditor stages. It persists inspectable run/trace artifacts. Local role
  implementations are deterministic until Foundry credentials are configured.

### Pressure index (`pressure-v1`)

This is a MatchPulse-defined metric, not an official Premier League metric.
For one trailing 300-second window, it is:

`min(100, 15 × attacking-third entries + 25 × high regains + 20 × penalty-box entries + 25 × shots/goals + 15 × pressure events)`.

The detector publishes a `pressure_shift` when the current index differs from
the preceding five-minute window by more than 25 points. Every published
insight records the calculated metric, exact source event IDs, time window,
state version, and deterministic validation checks.

## Run locally

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
uvicorn app.main:app --reload --port 8000
```

Run tests:

```bash
cd backend
python -m pytest
```

Run the connected web console in a second terminal:

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

The console calls the live backend APIs for a match ID. Until canonical events
have been ingested, it deliberately renders an empty "Awaiting events" state.

## API v1

- `GET /api/v1/health`
- `POST /api/v1/matches/{match_id}/events`
- `POST /api/v1/matches/{match_id}/events:batch`
- `GET /api/v1/matches/{match_id}/state`
- `POST /api/v1/import/statsbomb/{source_match_id}`
- `GET /api/v1/matches/{match_id}/events`
- `WS /api/v1/matches/{match_id}/live-stream`
- `GET /api/v1/matches/{match_id}/insights`
- `GET /api/v1/insights/{insight_id}`
- `GET /api/v1/insights/{insight_id}/evidence`
- `GET /api/v1/analysis-runs/{run_id}`
- `GET /api/v1/analysis-runs/{run_id}/trace`

The singular ingestion endpoint processes synchronously and returns
`published_insight_ids`, an intentional additive field to the proposed API
contract so a real UI can retrieve resulting insights immediately. Exact
duplicate events return `200` with `duplicate: true`; the same ID with a
different payload and out-of-order arrivals return `409`. Batch ingestion uses
explicit partial acceptance: structurally valid events are processed in input
order and business-rule rejections appear in `errors`; schema-invalid batches
return `422` before processing.

## Historical Hudl/StatsBomb Open Data

MatchPulse includes a replaceable adapter for the [Hudl/StatsBomb Open Data repository](https://github.com/hudl/open-data). Clone that repository locally, set `STATSBOMB_OPEN_DATA_ROOT` to its checkout, then import a completed match:

```bash
git clone https://github.com/hudl/open-data.git /path/to/open-data
export STATSBOMB_OPEN_DATA_ROOT=/path/to/open-data
curl http://localhost:8000/api/v1/import/statsbomb/matches
curl -X POST http://localhost:8000/api/v1/import/statsbomb/<source_match_id>
```

Imported events are normalized to `event-v1`, retain source IDs and metadata, and are sorted by match clock. The resulting match is marked `historical: true` and `live_feed_available: false`; the dashboard explicitly says live feed is unavailable. A future provider can publish the same canonical events without changing analytics or UI contracts.

## Known limits and next milestone

The service has a bounded two-window analytics cache, WebSocket live-transition
stream, best-effort optional Redis snapshot cache (`REDIS_URL`), deterministic
repair/fallback, an opt-in Foundry narrative adapter, and a Next.js console.
The browser console uses REST for its initial snapshot and WebSocket messages
for subsequent refreshes.

## Production configuration

Foundry is opt-in: install `pip install -e '.[foundry]'`, authenticate with
Azure identity, set `FOUNDRY_PROJECT_ENDPOINT`, `FOUNDRY_MODEL`, and
`MATCHPULSE_NARRATIVE_PROVIDER=foundry`. A 800 ms circuit breaker falls back to
the deterministic template. The model may propose copy only; metric values,
event IDs, and evidence windows stay deterministic and are audited.

The frontend supports Auth.js Google OAuth and a credentials provider. Set
`AUTH_SECRET`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and (only for the
credentials provider) `AUTH_CREDENTIALS_EMAIL`/`AUTH_CREDENTIALS_PASSWORD` in
`frontend/.env.local`. Credentials are appropriate for a controlled operator
account; user sign-up requires a durable identity store, which is not included.

Kubernetes manifests live in `k8s/`, with a companion initial Helm chart in
`helm/matchpulse/`. They require a real configured cluster to validate against
its API schema and deploy. GitHub Actions expects Azure/GitHub registry secrets
before it can publish images or roll AKS workloads.

The repository's planning context is retained in `matchpulse_context/`; the
five documents explicitly leave exact data-provider choice, agent package
version, auth, and durable-store configuration unresolved.
