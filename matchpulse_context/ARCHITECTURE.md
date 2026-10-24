# MatchPulse Architecture

## 1. Architectural principles

1. **Source independence:** event sources feed a canonical MatchPulse contract; analytics and agents must not depend on a single provider's raw schema.
2. **Deterministic facts, AI interpretation:** calculate metrics and validate references in code. Use AI for interpretation and narrative generation, not authoritative arithmetic.
3. **Evidence-first publication:** every published insight carries event references, a versioned evidence window, metrics, and validation metadata.
4. **Purpose-specific agents:** agent roles are differentiated by work and output contract.
5. **Observable orchestration:** users and evaluators can inspect the real run path, including outputs, handoffs, retries, validation, latency, and errors.
6. **Safe failure behavior:** malformed or unsupported output must not become a published fact.
7. **Incremental infrastructure:** prove an end-to-end local/deployable flow before adding event streaming infrastructure or unnecessary cloud services.
8. **Test from the beginning:** controlled fixtures are first-class test inputs, not the product's data-source architecture.

## 2. Recommended technology stack from the planning conversation

| Layer | Recommended technology | Responsibility / status |
|---|---|---|
| Frontend | Next.js, TypeScript, charting library | Match console, charts, evidence drawer, audience modes. Recommended, not confirmed as implemented. |
| Backend | Python, FastAPI | Event ingestion, schema validation, match analytics, orchestration API, query endpoints. Recommended, not confirmed as implemented. |
| Model platform | Microsoft Foundry models | Model calls for specialist analysis and narrative work. Model/deployment choice remains open. |
| Agent orchestration | Microsoft Agent Framework | Sequential/concurrent workflows, shared state, handoffs, failure management. Recommended, not confirmed as implemented. |
| Initial hosting | Azure Container Apps | Run backend and frontend/services as appropriate after local end-to-end behavior works. |
| Persistence | Azure Cosmos DB | Candidate for events, state snapshots, evidence, agent outputs, and verified stories. Schema/partitioning remains to be designed. |
| Observability | Azure Monitor / Application Insights and Foundry tracing | Correlate API, model, agent, duration, exception, and validation events where supported. |
| Optional event streaming | Azure Event Hubs | Defer until throughput or decoupled stream processing needs justify it. |
| Optional consumer | Azure Functions | Defer with Event Hubs until a real event-driven requirement exists. |

The stack is a recommendation recorded in the planning conversation, not evidence that any cloud resources or SDKs have already been configured. Inspect the repository and current Microsoft documentation before choosing exact package versions or implementation APIs.

## 3. Logical system diagram

```text
                    Replaceable Event Sources
      ┌──────────────────┬────────────────────┬─────────────────┐
      │ HTTP event input │ Automated test data │ Future provider │
      │ / source adapter │ / controlled fixture│ / data adapter  │
      └─────────┬────────┴──────────┬─────────┴────────┬────────┘
                └───────────────────┼──────────────────┘
                                    v
                         Event Ingestion API
                       Validate + normalize + dedupe
                                    |
                                    v
                         Canonical Event Store
                                    |
                                    v
                    Deterministic Match Intelligence
                    - match state and event ordering
                    - rolling windows and metrics
                    - significant-moment detection
                    - versioned evidence windows
                                    |
                      Significant moment / evidence
                                    v
                       MatchPulse Orchestrator
                         /               \
                        v                 v
                 Match Analyst     Tactical Analyst
                         \               /
                          \\ structured //
                            findings
                               |
                               v
                        Narrative Producer
                               |
                               v
                   Evidence Auditor + Validator
                    |          |           |
                  approve     repair    reject/fallback
                    |          |           |
                    └──────────┴───────────┘
                               |
                       Verified Story Ledger
                  (event refs, metrics, agent artifacts,
                   audit result, versions, timestamps)
                               |
                 ┌─────────────┼──────────────┐
                 v             v              v
             Fan View      Analyst View   Broadcast Output
                 \             |              /
                  └─────────────┼──────────────┘
                                v
                       Web Application / API
```

Cross-cutting concerns: persistence, trace correlation, structured logs, configuration versioning, bounded retries, error handling, and automated tests. The diagram describes the intended logical flow and not necessarily separate deployable microservices; keep the initial implementation modular without prematurely splitting every module into a service.

## 4. Main components and contracts

### 4.1 Event-source adapters

Purpose: translate input from a source into canonical events. Sources may include direct HTTP event submissions, test fixtures, a later full synthetic generator, or a permitted external dataset/provider.

Responsibilities:
- Map provider/source identifiers and field names into canonical identifiers.
- Normalize timestamps, event types, team/player IDs, and spatial coordinates where possible.
- Declare missing fields rather than fabricate them.
- Preserve source provenance and, if practical, the source payload or a normalized audit representation.
- Avoid importing provider-specific assumptions into the metrics engine or agents.

A later adapter may need to handle different pitch coordinate conventions, clock conventions, event taxonomies, and player identity systems. The exact adapter requirements depend on the selected data source and should not be guessed ahead of time.

### 4.2 Event ingestion API

Purpose: validate and accept canonical events, assign/confirm event ordering, and invoke or enqueue deterministic state updates. The earliest implementation can process a small batch synchronously if that keeps the complete path simple. Do not add a broker solely to imitate production streaming.

Key qualities:
- Schema validation with explicit errors.
- Match-scoped ordering rules.
- Duplicate-aware handling of stable event IDs.
- Correlation/request IDs for diagnostics.
- A clear distinction between accepted events and downstream intelligence processing status.

### 4.3 Deterministic Match Intelligence Engine

Purpose: produce reproducible facts and identify candidate moments.

Responsibilities:
- Update match state based on ordered canonical events.
- Calculate documented metrics using deterministic functions.
- Maintain time/event windows for before-and-after comparisons.
- Detect significant state changes using thresholds/rules stored in configuration.
- Create evidence windows with the exact event IDs and metric/state version used.

The engine should produce facts and candidate-analysis inputs. It must not write the final prose narrative or depend on the LLM to compute official metrics.

### 4.4 Agent orchestrator

The coordinator controls a workflow comprising:

1. Create an immutable/versioned evidence snapshot for the candidate moment.
2. Run Match Analyst and Tactical Analyst concurrently when their shared inputs allow it.
3. Validate their structured outputs against schemas and available data.
4. Pass structured findings to the Narrative Producer.
5. Run deterministic checks and semantic review through the Evidence Auditor.
6. If invalid, request one repair by default.
7. If the repair fails, use a conservative fallback derived from known facts, or suppress the insight.
8. Save the outcome, all useful artifacts, and trace metadata to the ledger.

A late-running agent must not accidentally produce an insight against a newer match state while citing an older snapshot. All agents in one run must identify the same match-state/evidence-window version.

### 4.5 Match Analyst

Input: versioned match state, computed metric changes, significant-moment candidate, relevant event references, and metric definitions.

Output should be structured, for example:
- summary of measured changes;
- metrics and before/after values;
- relevant event IDs/window;
- observations separated from interpretation;
- missing information or caveats.

The Match Analyst should not recalculate the authoritative values. It can interpret and select facts from the supplied deterministic results.

### 4.6 Tactical Analyst

Input: the same evidence snapshot plus relevant event sequences, zone/territory information, possession transitions, and available control/chaos features.

Output should include:
- one or more tactical hypotheses;
- supporting events/features;
- contradicting or missing evidence where identified;
- confidence/caveats;
- claims that would be unsafe to present as established facts.

Tactical explanation should avoid unsupported causal claims. For example, the presence of four high regains plus a pressure increase may be consistent with sustained pressure, but alone it may not prove that a specific tactical instruction caused the change.

### 4.7 Narrative Producer

Input: validated structured findings and evidence; requested audience modes/languages/preferences.

Output:
- common insight/fact references;
- headline and concise summary;
- what changed;
- why it matters;
- evidence references;
- audience-specific variants;
- next-watch prompt if useful and supported;
- explicit uncertainty/limitations as needed.

The Producer must not introduce new unreferenced metrics or event claims. Audience adaptation changes presentation, not the authoritative facts.

### 4.8 Evidence Auditor and deterministic validator

The validator is not a single LLM call. Separate deterministic checks from semantic review.

Deterministic checks should include:
- every event ID exists;
- cited events belong to the correct match and declared window;
- numeric claims match the stored metrics/state or defined tolerances;
- time windows and metric names are valid;
- required fields and output schema are valid;
- no contradictory or missing mandatory references are silently accepted.

Semantic review can flag whether a proposed interpretation appears unsupported, contradictory, overstated, or insufficiently qualified. Semantic approval is not mathematical proof of causality.

The audit record should identify approved/repaired/rejected status and actionable reasons. Retry count must be bounded.

### 4.9 Verified Story Ledger

Store the canonical published story plus supporting artifacts. Preserve the relationship between the narrative, event IDs, deterministic calculations, input state version, each agent's output, validation decisions, and the final publication decision.

This ledger powers the Show Evidence UI, auditing, replay, and evaluation. It should be persisted or reconstructable from durable application records, not fabricated client-side demo data.

### 4.10 Presentation layer

The frontend should render facts from backend APIs:
- event ticker and match context;
- pressure/control indicators and charts;
- significant-moment timeline;
- insight card;
- evidence drawer;
- agent activity panel;
- Fan/Analyst/Broadcast modes;
- preferences such as favorite team/player and language;
- explicit empty, loading, rejected, fallback, and error states.

Use a single verified fact payload as the common source for all audience views. Different views can have different display schemas, but values and event references must remain consistent.

## 5. Metrics definitions to be designed and documented

The planning discussion identified these initial metrics, but it did not settle complete formulas. Implementations must define, document, and unit test the formulas instead of implying they are already specified.

### Pressure index

- Project-defined 0-100 score.
- Candidate inputs: attacking-third entries, high regains, penalty-box entries, shots.
- Compare rolling five-minute window with previous five-minute window.
- Normalize inputs and define weights, clipping, empty-window behavior, and missing-data behavior.
- Label it as a MatchPulse metric rather than an official Premier League metric.

### Control versus chaos

- Candidate inputs: possession-sequence length, turnovers, passing completion, rapid transitions.
- Define the formula/categories and establish tests using known fixtures.

### Pass quality/difficulty

- Candidate inputs: pass distance, angle, completion, synthetic opponent-pressure information.
- Define behavior when coordinates or pressure fields are unavailable. Do not generate precise pass difficulty claims from incomplete evidence.

## 6. Proposed repository structure

This is a proposed modular-monolith starting point, not an existing verified tree. Adapt it to the current repository after inspection. Avoid unnecessary packages or services until the full flow needs them.

```text
matchpulse/
├── apps/
│   └── web/                         # Next.js + TypeScript UI
│       ├── app/                     # routes/pages (if App Router is chosen)
│       ├── components/
│       │   ├── match-console/
│       │   ├── insights/
│       │   ├── evidence/
│       │   └── agent-activity/
│       ├── lib/                     # API client, schema/types
│       └── tests/
├── services/
│   └── api/                         # FastAPI application
│       ├── app/
│       │   ├── main.py
│       │   ├── api/                 # route handlers
│       │   ├── schemas/             # API/Pydantic contracts
│       │   ├── ingestion/           # canonicalization/source adapters
│       │   ├── intelligence/        # state, metrics, detection, evidence
│       │   ├── agents/              # four agents and contracts
│       │   ├── orchestration/       # coordination/retry/fallback
│       │   ├── ledger/              # story/event persistence abstraction
│       │   ├── observability/       # trace/correlation setup
│       │   └── config.py
│       └── tests/
│           ├── unit/
│           ├── integration/
│           └── evaluation/
├── packages/
│   └── contracts/                   # only if cross-language/shared schemas justify it
├── tests/
│   └── fixtures/                    # small synthetic, deterministic test events
├── docs/
│   ├── PROJECT_OVERVIEW.md
│   ├── REQUIREMENTS.md
│   ├── ARCHITECTURE.md
│   ├── API_SPEC.md
│   └── TECH_DECISIONS.md
├── infra/                           # deployment configuration when required
├── .env.example
├── README.md
└── ...
```

Do not force a monorepo or this exact tree if the repository already has a coherent structure. The key requirement is to keep the event source, deterministic intelligence, orchestration, persistence, and UI responsibilities distinct.

## 7. Data flow

1. A source adapter or caller submits one/more events.
2. FastAPI validates and normalizes them into canonical events.
3. The ingestion layer applies duplicate/order rules and stores the accepted event records.
4. The intelligence engine updates the appropriate match state and deterministic metrics.
5. The detector determines whether a meaningful moment exists. A valid outcome is either a candidate moment or no insight.
6. If a candidate exists, the engine creates an immutable evidence snapshot with time range, metric values, and event IDs.
7. The orchestrator runs the specialist agents against that snapshot.
8. The Narrative Producer generates proposed story variants.
9. Deterministic validation checks references/numbers/schema; semantic review evaluates whether interpretation is overclaimed.
10. The coordinator approves, repairs once by default, or falls back/suppresses.
11. The ledger records the decision and artifacts.
12. The API returns the processing result and/or the UI retrieves published insights and evidence.
13. The frontend renders audience-specific variants and provides access to evidence and activity traces.
14. Trace IDs tie together the original event, state version, agent calls, validation, and published insight.

## 8. Persistence design direction

Cosmos DB was the recommended option in the conversation, but its concrete schema and partition strategy have not been decided. Keep persistence behind repository interfaces so local tests do not require a cloud database and so the exact storage choice can be adjusted.

Logical record types likely include:
- canonical events;
- current match state and/or state snapshots;
- metric/evidence windows;
- agent execution records;
- candidate and verified insights;
- user preferences, if persistence is needed;
- run/trace metadata.

A match-scoped partition is a plausible starting point for match data, but validate query patterns, event volume, retention, and cross-match operations before committing to a final Cosmos DB partition key. Do not put large duplicated source payloads into every insight unless there is a concrete query/audit need.

## 9. Deployment and infrastructure sequence

### Initial stage

- Run API, UI, and tests locally.
- Use a local/test persistence adapter where appropriate.
- Configure model access through environment variables/secret configuration, not hardcoded credentials.
- Build a minimal complete event-to-insight path.

### Deployment stage

- Deploy the API and UI/service components to Azure Container Apps as justified by the deployment arrangement.
- Configure persistence and tracing.
- Verify all required secrets/settings in the deployment environment.
- Run the same integration/evaluation suite against the deployed configuration.

### Optional scale/event-driven stage

Consider Event Hubs plus an Azure Functions consumer only after measured throughput, buffering, decoupling, or asynchronous-processing requirements justify them. They should not block the working product or become decorative infrastructure.

## 10. Security, configuration, and operational behavior

- Do not commit model API keys, database credentials, or Azure secrets.
- Validate all event and agent payloads against typed schemas.
- Bound model retries and request execution time.
- Treat source data and model outputs as untrusted input.
- Store enough diagnostics to understand failures without logging unnecessary sensitive data.
- Add trace/correlation identifiers to event processing and orchestration.
- Version metric formulas, threshold configuration, event contract, and narrative schema when changes could alter previous output.
- Distinguish “no meaningful insight found” from API failure or processing failure.
- A deployment may not claim production readiness until operational testing and failure behavior have been verified.
