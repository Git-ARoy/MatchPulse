# MatchPulse Technical Decisions and Rationale

## How to read this document

This file records choices and rejected approaches explicitly discussed in the planning conversation. It distinguishes decisions that were made from recommendations that remain open. The intent is to prevent a coding agent from repeatedly proposing approaches already ruled out without new evidence.

## TD-001: Build the product around a source-independent event contract

**Status:** Direction agreed.

**Decision:** Build MatchPulse around a canonical event schema, an ingestion API, deterministic intelligence engine, multi-agent workflow, evidence ledger, and UI. Keep event-source adapters replaceable.

**Alternatives considered:**
- Couple the application directly to a synthetic simulator's event format.
- Make the architecture depend on whichever public/live dataset is selected first.

**Why those alternatives were rejected:** They would make the central pipeline dependent on a temporary or not-yet-selected source and force avoidable redesign when changing datasets/providers.

**Implementation consequence:** The ingestion/adapter layer owns source-specific mapping. Core metrics and agents consume canonical events and versioned evidence snapshots.

## TD-002: Do not make a full synthetic match simulator the first product deliverable

**Status:** Direction agreed, with an important testing qualification.

**Decision:** First build the actual MatchPulse application and its contracts. Test components and the end-to-end pipeline, then evaluate whether a full simulator, additional synthetic data, a properly licensed dataset, or a suitable provider is the right next step.

**Alternative considered:** Start by creating a simulator and build the rest of the product around its generated stream.

**Why rejected:** The simulator would dictate the initial design and consume time before the core intelligence and orchestration are proven.

**Qualification:** Controlled synthetic fixtures are still required to test known states, pressure changes, quiet periods, malformed payloads, and failure paths. Do not confuse “no simulator-first product” with “no test data.” The hackathon brief described in the conversation requires synthetic, football-realistic data, so final-submission data must be checked against official rules.

## TD-003: Use deterministic code for authoritative football metrics

**Status:** Direction agreed.

**Decision:** Calculate metrics such as event counts, rolling pressure values, possession-related statistics, and before/after values in deterministic code. Let agents interpret them.

**Alternative considered:** Ask an LLM to calculate metrics or invent a pressure index from the event stream.

**Why rejected:** LLM arithmetic can be inconsistent, hard to reproduce, and difficult to audit. A generated number without a reproducible formula defeats the product's evidence-first promise.

**Implementation consequence:** Metrics need documented formulas, version identifiers, unit tests, and evidence references. Do not represent MatchPulse-defined metrics as official Premier League methodology.

## TD-004: Build a real multi-agent workflow with distinct responsibilities

**Status:** Target architecture agreed; exact implementation remains to be built/verified.

**Decision:** Use four agents coordinated through an explicit workflow:
1. Match Analyst.
2. Tactical Analyst.
3. Narrative Producer.
4. Evidence Auditor.

The first two can analyze the same immutable evidence window concurrently. The Producer uses their structured findings, and the Auditor/validator decides whether the proposed narrative is publishable.

**Alternatives considered:**
- One generic chatbot/summary prompt.
- Multiple agents that merely repeat the same summarization task.
- A diagram that claims multi-agent behavior without actual structured handoffs.

**Why rejected:** These alternatives fail to show a genuine orchestration contribution and do not provide a credible division of responsibilities.

**Implementation consequence:** Define typed input/output schemas, shared state/versioning, explicit handoffs, observable run traces, bounded retries, and a useful evaluation demonstrating the value of the workflow.

## TD-005: Separate factual validation from semantic review

**Status:** Recommended refinement of the agreed Evidence Auditor design.

**Decision:** Deterministically validate all numerical claims, metric values, event IDs, match IDs, time windows, schemas, and other checkable references. Use an AI/semantic review only for interpretive concerns that cannot be resolved with simple exact checks.

**Alternative considered:** Trust a second LLM to certify the first LLM's claims as correct.

**Why rejected:** Two models can share the same mistaken assumption. Semantic review cannot prove a statistic or causal claim merely by agreeing with it.

**Implementation consequence:** The auditor's result should include machine-checkable validation outcomes and separately labeled semantic findings. Do not equate “LLM approved” with “factually proven.”

## TD-006: Publish only evidence-backed narratives; otherwise repair, fall back, or suppress

**Status:** Direction agreed.

**Decision:** Every published narrative is linked to its supporting metrics and source event references. If the Auditor rejects a claim, allow one repair attempt by default. If repair fails, produce a deterministic event-based fallback when safe, or suppress the speculative insight.

**Alternative considered:** Show a plausible model-generated narrative even when supporting evidence is incomplete or contradictory.

**Why rejected:** Unsupported claims undermine the platform's primary differentiator and create a failure mode that is hard to inspect or defend to judges.

**Implementation consequence:** Record rejected claims/reasons, retry count, final status, and fallback/suppression result in the evidence/run ledger. Tests must cover each branch.

## TD-007: Implement audience modes over one verified fact set

**Status:** Direction agreed.

**Decision:** Provide Fan, Analyst, and Broadcast variants based on the same approved underlying insight/evidence.

**Alternative considered:** Generate separate narratives independently for each audience without enforcing factual consistency.

**Why rejected:** Independent generation risks inconsistent scores, metric values, time windows, and event claims.

**Implementation consequence:** Separate the canonical verified insight/facts from presentation variants. Personalization changes relevance and detail, not the underlying match facts.

## TD-008: Build the evidence ledger and inspection UI as a first-class feature

**Status:** Direction agreed.

**Decision:** Give each insight a **Show Evidence** action that exposes source event IDs, the time window, before/after values, original agent outputs/handoffs, and the validation decision.

**Alternative considered:** Show only the final narrative plus a static diagram of the agents.

**Why rejected:** A polished narrative alone does not establish factual grounding or demonstrate real agent orchestration.

**Implementation consequence:** Preserve the artifacts needed to reconstruct why an insight was published. The frontend must read these records from actual backend state, not from hardcoded mock activity.

## TD-009: Prioritize core pipeline over extra Azure infrastructure

**Status:** Direction agreed.

**Decision:** Start with the smallest viable application that proves event ingestion, deterministic analytics, agent collaboration, validation, and a real UI. Deploy the working application, then add streaming/cloud services when required.

**Alternatives considered:** Add Azure Event Hubs and Azure Functions before the core pipeline works; expand infrastructure to make the architecture look more sophisticated.

**Why rejected:** Infrastructure does not compensate for weak intelligence or an unfinished application, and it can consume the short hackathon schedule.

**Implementation consequence:** The proposed initial stack is Next.js/TypeScript, FastAPI/Python, Microsoft Foundry, Microsoft Agent Framework, Azure Container Apps, and potentially Cosmos DB and Application Insights. Event Hubs and Functions are conditional extensions, not initial requirements.

## TD-010: Treat the simulator as a test/demo utility only if later justified

**Status:** Conditional.

**Decision:** A fuller generator may be created after the core product works if it enables repeatable scenario playback or a useful demo. It should feed the same canonical API and not become a special alternate architecture.

**Why:** Deterministic, reproducible scenarios are useful for tests and demonstrations, but the simulator should not constrain the product design.

## TD-011: Select external data only after the pipeline has measurable gaps

**Status:** Agreed sequence; source choice unresolved.

**Decision:** After testing, evaluate a fuller synthetic dataset/generator, a properly licensed public dataset, or a compatible live event provider based on the actual test results and product requirements.

**Alternatives considered:** Commit now to a particular public/live source before the canonical contract and intelligence engine work.

**Why deferred:** No provider/dataset has been selected or verified in the conversation. Availability alone does not establish license rights, fit with the canonical event schema, sufficient event fields, or competition compliance.

**Implementation consequence:** Do not add provider-specific assumptions now. When considering a source, assess licensing/use rights, final competition rules, schema coverage, spatial/time conventions, player identity, latency, cost, and reproducibility.

## TD-012: Test incrementally and evaluate restraint, not just detection

**Status:** Recommended engineering practice based on the stated acceptance criteria.

**Decision:** Add unit, integration, agent-failure, and end-to-end tests as components are implemented. Include scenarios in which no insight should be produced.

**Alternative considered:** Build most of the system first and reserve a final phase for broad testing.

**Why rejected:** Errors in event contracts, metrics, or orchestration discovered late can force expensive redesign. A system that creates an insight for every event is not reliably intelligent.

**Implementation consequence:** Test known metric values, seeded pressure changes, quiet periods, invalid numerical claims, unknown event IDs, malformed agent output, timeouts, retries, fallback, and cross-audience consistency. Report measured results only.

## TD-013: Use the official synthetic-data and media rules as submission constraints

**Status:** Constraint stated in the source conversation; current official rules still require verification.

**Decision:** The hackathon submission must use synthetic, football-realistic data as required by the challenge description. The final demo should use fictional team names/custom visuals and avoid unlicensed Premier League footage, crests, trademarks, music, or other copyrighted material.

**Alternative considered:** Assume a real-match public feed can automatically replace synthetic data in the final submission.

**Why rejected:** The challenge description explicitly required synthetic data and stated that real Premier League match data is not redistributed to participants. Public availability does not itself guarantee authorization or eligibility.

**Implementation consequence:** Development may evaluate properly licensed real data only after checking the relevant terms, but the final dataset/demo must comply with official rules. Verify all rules before final submission.

## TD-014: Make the project inspectable and reproducible for judges

**Status:** Direction agreed.

**Decision:** Provide a public repository, reproducible setup/testing instructions, architecture documentation, a working deployment/demo where practical, and a demonstration video under two minutes.

**Alternative considered:** Rely on a presentation of the architecture without a working flow or inspectable source.

**Why rejected:** The stated rubric gives equal weight to implementation, agentic design, impact, UX/presentation, and category adherence; source and working behavior matter.

**Implementation consequence:** The README should describe actual implemented features and tested outcomes. The demo should show the real event-to-insight pipeline, meaningful agent handoffs, personalized views, evidence validation, and a rejection/repair or fallback case within the available time.

## Open decisions not to invent

These points were not settled by the conversation and must be decided from repository inspection, implementation needs, tests, and official documentation:

- Current repository structure and what code is already implemented.
- Exact canonical event enum list, schema versioning and coordinate conventions.
- Precise formulas/weights/normalization for pressure, control-versus-chaos, and pass difficulty.
- Whether analysis is triggered automatically on ingestion or by explicit API request, or both.
- Exact API paths and response schemas in the deployed code.
- Exact authentication/authorization approach.
- Whether Cosmos DB is required for the first working increment or a local adapter is sufficient.
- Cosmos DB container design, partition keys, indexing, retention, and cost.
- Specific Foundry model/deployment and supported context/structured-output capabilities.
- Exact Microsoft Agent Framework package/version and orchestration APIs.
- Production latency SLA, throughput target, retention period, budget, and Azure credits.
- External data provider or dataset, licensing, and final submission data strategy.
- Supported output languages and localization mechanism.
- Whether video-based automatic eventing is in scope.
- Exact official prize track naming and deadline at the time of submission.

When making one of these decisions, document the rationale and update this file instead of silently allowing the implementation to drift.
