# MatchPulse

MatchPulse is an evidence-first football intelligence platform for synthetic,
football-realistic events. The product path in this repository ingests
fictional events, calculates deterministic match state, validates evidence,
and renders audience-specific verified insights. It does not redistribute real
Premier League match data or use an LLM as the source of statistics.

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
- A connected Next.js studio console with a synthetic scenario launcher, event
  ticker, evidence-linked insight timeline, fan/analyst/broadcast modes,
  player focus, English/Spanish recaps, and a tactical event radar.

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

The console calls the live backend APIs. Select **Momentum surge** to ingest a
small fictional sequence through the same path used by external events; select
**Quiet period** to see deliberate non-publication when no threshold is met.

## API v1

- `GET /api/v1/health`
- `GET /api/v1/demo/scenarios`
- `POST /api/v1/demo/scenarios/{scenario_id}`
- `POST /api/v1/matches/{match_id}/events`
- `POST /api/v1/matches/{match_id}/events:batch`
- `GET /api/v1/matches/{match_id}/state`
- `POST /api/v1/import/statsbomb/{source_match_id}`
- `GET /api/v1/matches/{match_id}/events`
- `WS /api/v1/matches/{match_id}/live-stream`
- `GET /api/v1/matches/{match_id}/insights`
- `GET /api/v1/matches/{match_id}/recap?audience=fan&language=en`
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

## Synthetic demo data policy

The product demo uses only authored fictional teams, players, events, and
metrics. It is deliberately small, inspectable test data rather than a full
match simulator. Use the public scenario API to exercise the five-stage
hackathon path:

```bash
curl http://localhost:8000/api/v1/demo/scenarios
curl -X POST http://localhost:8000/api/v1/demo/scenarios/momentum-surge
curl http://localhost:8000/api/v1/matches/synthetic_ridge_harbor/state
curl http://localhost:8000/api/v1/matches/synthetic_ridge_harbor/insights
```

The source adapter boundary remains provider-independent for future licensed
or permitted integrations. Historical-data adapters are not part of the
hackathon demo path and must not be used to supply the submission experience.

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
`helm/matchpulse/`. GitHub Actions always verifies and publishes images on a
main-branch push. It rolls AKS workloads only when repository variable
`DEPLOY_TO_AKS=true` and the `AZURE_CREDENTIALS`, `AZURE_RESOURCE_GROUP`, and
`AKS_CLUSTER_NAME` secrets are configured. This keeps ordinary source pushes
from failing because a deployment environment has not been provisioned.

The repository's planning context is retained in `matchpulse_context/`; the
five documents explicitly leave exact data-provider choice, agent package
version, auth, and durable-store configuration unresolved.
