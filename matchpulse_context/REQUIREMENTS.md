# MatchPulse Requirements and Feature Plan

This document converts the planning conversation into implementation requirements. Priority labels are planning guidance: **P0** = required for a credible end-to-end product; **P1** = high-value after P0 works; **P2** = optional extension. They are not official hackathon categories.

## 1. Product-level requirements

### P0: Canonical events and ingestion

- Accept football events from an HTTP API.
- Validate required identifiers and event attributes.
- Normalize source-specific input into a canonical MatchPulse event schema.
- Preserve stable event IDs, match IDs, timestamps, team/player references, event type, and relevant spatial/context fields.
- Reject malformed input with useful validation errors; do not silently invent required data.
- Make ingestion independent of the source. Source adapters must be responsible for mapping provider-specific fields into the canonical contract.
- Support idempotent or duplicate-aware ingestion using stable event IDs. Exact duplicate behavior should be documented and tested.
- Maintain an ordered, queryable event history per match, including the source event references used by each insight.

### P0: Deterministic match-state and analytics engine

- Update match state as normalized events arrive.
- Calculate core metrics with ordinary deterministic code, not LLM arithmetic.
- Track possession changes/transitions and event counts where the available schema supports them.
- Support rolling event/time windows so the system can compare recent behavior with a preceding window.
- Detect significant moments using explicit thresholds or documented rules.
- Generate an evidence window containing the relevant event IDs, time range, metric values, and state version.
- Keep metric calculations reproducible from the same ordered events.
- Expose metric formulas and definitions in documentation and, where suitable, the UI.
- Avoid claiming that project-defined metrics are official Premier League metrics. The pressure index in the planning conversation is a MatchPulse-defined metric.

### P0: Initial intelligence concepts

The first documented concepts discussed are:

1. **Pressure index:** a documented 0-100 project-defined index using normalized features such as attacking-third entries, high regains, penalty-box entries, and shots. Compare a rolling five-minute window with the preceding five-minute window. Choose and document a specific formula during implementation; the conversation does not establish final weights or exact normalization.
2. **Control versus chaos:** characterize play using possession-sequence length, turnovers, passing completion, and rapid transitions. The exact formula/category boundaries remain to be designed and tested.
3. **Pass quality:** estimate difficulty from pass distance, angle, completion outcome, and synthetic opponent-pressure information where those fields exist. Do not make unsupported claims if inputs are missing.

The engine should explicitly identify unavailable/insufficient data. It must not substitute fabricated fields for absent source facts.

### P0: Multi-agent analysis and orchestration

Implement four purpose-specific agents coordinated by one workflow:

- **Match Analyst:** identify material changes in metrics/momentum and return structured findings with metric values and event references.
- **Tactical Analyst:** investigate event sequences, territorial patterns, transitions, and control-versus-chaos behavior. Return hypotheses with supporting evidence and calibrated uncertainty; do not state unobserved causes as facts.
- **Narrative Producer:** use the structured findings and shared evidence to generate the insight and its audience-specific variants.
- **Evidence Auditor:** audit claims and evidence. Deterministic checks must verify numeric claims, event references, and time windows. Semantic checks can flag unsupported interpretation, overstatement, or contradictions.
- **Coordinator:** manage shared/versioned input state, concurrent analysis where appropriate, handoffs, timeouts, bounded retries, and the final publish/fallback/suppress decision.

The system must prove real orchestration in its output/trace, not merely label several prompts as different agents. Every agent needs a defined input/output schema and a unique responsibility.

### P0: Evidence ledger and factual safeguards

Every published insight must preserve:

- Insight ID and version.
- Match ID and match-state/evidence-window version.
- Time window and supporting event IDs.
- Before-and-after metric values used in the narrative.
- Structured outputs from the specialist agents.
- Narrative versions generated for supported audiences.
- Auditor/validator decision, findings, and whether a repair occurred.
- Retry count and fallback/suppression status when applicable.
- Creation time and processing/latency metadata where available.

Rules:

- Validate each explicit numerical claim against deterministic computed state.
- Validate every cited event ID and ensure it belongs to the expected match and evidence window.
- Do not publish a narrative when its essential claims are invalid.
- Give the Narrative Producer at most one repair attempt by default, as proposed in the conversation. Make the limit configurable and test it.
- After a failed repair, publish a conservative deterministic, event-based fallback if it can be constructed safely; otherwise suppress the speculative insight.
- A semantic auditor must not be treated as proof that a causal interpretation is true.

### P0: End-to-end product path

The first end-to-end milestone is a real application flow, not a simulator demo:

1. Submit a small valid set of events to the API.
2. Validate and normalize events.
3. Update match state and calculate metrics.
4. Detect a meaningful moment when warranted.
5. Run agent analysis and narrative generation.
6. Validate the proposed insight.
7. Save/persist or otherwise expose the verified insight and evidence.
8. Return the insight to the UI/API consumer.

At least one controlled fixture should exercise a clear pressure swing. Another should represent a quiet period where the system does not manufacture an insight. These fixtures are test data, not a requirement to ship a full match simulator as a product feature.

### P0: User experience

The frontend should provide the following core views/components:

- **Live Match Console:** match clock, scoreline, event ticker, pressure chart, possession transitions, and significant-moment timeline. Play/pause/replay controls are useful for deterministic demonstration, but should not force a full simulator into the architecture.
- **Explainable Insights:** short headline, what changed, why it matters, evidence links, supporting statistics, and a concise next-watch prompt where supportable.
- **Show Evidence / Evidence Drawer:** reveal source event IDs, match-time window, before-and-after values, and the validation outcome.
- **Agent Activity Panel:** show which agents ran, their structured findings/handoffs, validation result, retries, and measured latency.
- **Audience modes:** Fan, Analyst, and Broadcast. All modes must derive from the same verified underlying facts.
- **Preference controls:** favorite fictional team/player and language preference. User preferences can change presentation and relevance, but must not modify the authoritative event facts.
- **Broadcast payload:** machine-readable output suitable for a downstream graphics/overlay renderer. Define and version its schema.
- **Clear loading/error states:** show processing, partial failure, rejection, fallback, and absence-of-insight states instead of presenting stale or unsupported text as current.

### P0: Evaluation and tests

Build an automated test suite incrementally. At minimum, cover:

- Canonical schema validation and invalid payload behavior.
- Duplicate event handling and event ordering.
- Deterministic metric calculations and known expected values.
- Correct rolling-window boundaries.
- Detection of a seeded, meaningful pressure change.
- No unnecessary insight during a quiet period.
- Event-reference and numeric-claim verification.
- Missing fields and insufficient evidence.
- Malformed agent JSON/schema violations.
- Agent timeout/failure and bounded retries.
- Auditor rejection followed by repair.
- Repair failure leading to deterministic fallback or suppression.
- Consistency of factual values across audience modes.
- API integration from event ingestion through returned insight.

Report actual test results in project documentation; do not invent accuracy, quality, or latency figures before measurement.

## 2. P1 requirements

- Persist events, match-state snapshots, evidence windows, agent outputs, and verified stories. Azure Cosmos DB was the recommended initial persistence option, subject to deployment and project constraints.
- Add trace correlation across API request, match-state update, agent execution, validation, and publication.
- Capture model calls, tool calls, durations, and errors through appropriate Foundry tracing and Azure Monitor/Application Insights integrations where available.
- Provide a replay or controlled playback mechanism to reproduce a known event sequence and inspect the exact resulting insights.
- Support automated match recaps based on an explicitly selected time range or a completed match-state record.
- Add multilingual narrative generation for supported languages, preserving the same verified facts across translations.
- Add personalized player-focused mode and selected performance-metric preference.
- Make significant-moment thresholds configurable and version their configurations.
- Provide README, architecture documentation, environment setup instructions, tests, and repeatable deployment instructions.

## 3. P2 / conditional extensions

Add these only after the end-to-end core is reliable and there is a specific requirement:

- Azure Event Hubs for higher-throughput event ingestion.
- Azure Functions as an event-processing consumer.
- More elaborate live-stream integrations or automatic event generation from video.
- A full synthetic match generator as a development/demo utility.
- A licensed public dataset or live event provider adapter after data availability, usage rights, schema fit, and final competition rules are checked.
- More sophisticated player speed/distance indicators, ball/shot speed metrics, and automated video eventing. These were mentioned in the challenge options, but the discussion did not establish them as core MVP commitments.

## 4. User stories / use cases

### Live pressure-shift insight

As a broadcaster or fan, I want MatchPulse to alert me when a team's attacking pressure changes materially, so that I understand why the match is changing rather than seeing an isolated statistic.

Acceptance criteria:
- A change is calculated from actual events in a known window.
- The output includes the before/after metric and relevant event IDs.
- A narrative explains the significance without overclaiming causality.
- If the evidence checks fail, the narrative is repaired, replaced with a safe fallback, or suppressed.

### Inspect an insight's evidence

As an analyst or judge, I want to open a published insight and inspect its metrics, event IDs, window, agent findings, and audit status, so that I can verify how the system reached the conclusion.

Acceptance criteria:
- Evidence comes from persisted or traceable application state, not UI-only mock content.
- All references resolve to the correct match and window.
- The interface differentiates agent hypotheses from deterministic facts.

### Reuse verified facts for different audiences

As a user, I want Fan, Analyst, and Broadcast modes to present the same match facts with different levels of detail and formatting, so that the output suits my task without contradicting other views.

Acceptance criteria:
- The verified evidence payload is shared across modes.
- Numerical values, time windows, and cited events remain consistent.
- Broadcast output is compact and schema-conforming; Analyst output includes detailed evidence; Fan output uses accessible language.

### Reject an unsupported claim

As an evaluator, I want the application to expose an invalid or unsupported narrative and demonstrate its rejection/repair path, so that the multi-agent system's safety behavior is observable.

Acceptance criteria:
- A deterministic test can induce an invalid claim or bad event reference.
- The validator/auditor records the reason for rejection.
- Retry count is bounded.
- The final result is a repaired valid insight, safe fallback, or explicit suppression.

### Integrate a future event source

As a developer, I want to add a dataset/provider adapter without rewriting core analytics, agents, or UI, so that MatchPulse can be evaluated against another valid source after the initial pipeline is built.

Acceptance criteria:
- The adapter maps source fields to the canonical schema.
- Source-specific logic is isolated from the analytics/agent layers.
- Compatibility and missing-field behavior have tests.

### Avoid false positives in quiet periods

As a broadcaster or fan, I do not want an insight every time an event arrives; I want the system to remain quiet when no meaningful change is supported.

Acceptance criteria:
- A quiet fixture does not trigger an unsupported narrative.
- Detection thresholds are explicit and testable.
- Absence of insight is treated as a valid outcome, not an application error.

## 5. Constraints and delivery considerations

- The planning conversation had an aggressive hackathon timeline: October 22 through October 27, 2026, with a deadline recorded as October 27 at 11:59 PM Pacific Time. Verify this against official sources before treating it as current.
- The demo video must be under two minutes and must show the application actually functioning.
- The GitHub repository must be public for submission.
- Synthetic, football-realistic data is a stated challenge requirement. Do not assume real data is an acceptable final substitute.
- No budget or available Azure credits were established in the conversation. Prefer a minimal deployable baseline; avoid unbounded model calls and unnecessary cloud resources.
- No real event provider, dataset, authentication provider, or production availability target has been selected.
- The project should be responsive enough to demonstrate live-play use, but no concrete latency SLA was established. Measure actual latency before stating a target or claim.
- No specific supported language list has been selected.

## 6. Product acceptance checklist

- [ ] Real HTTP ingestion path accepts valid canonical events.
- [ ] Events update deterministic match state and metrics.
- [ ] Meaningful event windows and significant moments are detected.
- [ ] Four-agent workflow has distinct contracts and inspectable handoffs.
- [ ] Numerical and event-reference claims are validated deterministically.
- [ ] Rejection, repair, retry limit, fallback, and suppression paths are tested.
- [ ] Verified stories expose a complete evidence trail.
- [ ] Fan, Analyst, and Broadcast outputs derive from one verified fact set.
- [ ] Quiet-period behavior prevents manufactured insights.
- [ ] UI is backed by real APIs rather than only hardcoded demonstration content.
- [ ] Core flow is reproducibly testable and documented.
- [ ] Final data and media comply with the official hackathon rules.
- [ ] Public repository, pitch, and under-two-minute demo are ready.
