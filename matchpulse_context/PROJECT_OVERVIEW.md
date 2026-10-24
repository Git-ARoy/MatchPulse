# MatchPulse: Evidence-First Multi-Agent Football Intelligence

## 1. Project summary

MatchPulse is a football intelligence platform that transforms incoming football-match events into explainable, evidence-backed, audience-specific insights. Its intended inputs include events such as passes, shots, tackles, possession changes, high regains, pressure events, player and match metadata, and related football-realistic data.

The product is not intended to be just a statistics dashboard or a chatbot that summarizes a match. MatchPulse should detect meaningful changes in the state of a match, calculate the relevant facts deterministically, investigate plausible tactical context, explain why the change matters, validate the claims against recorded evidence, and render the verified insight for different audiences.

The project is being developed for the Microsoft × Premier League **Inside the Game: Developer Hackathon**, specifically with a strategy focused on the **Best Multi-Agent System / Orchestration** prize track rather than relying on the grand prize. The exact available prize categories and rules should be checked against the current official hackathon page before submission; the category named in the source conversation was the intended primary target.

## 2. Problem statement

Raw event feeds and conventional football dashboards expose facts but often do not explain the developing story. A dashboard may say that a team has 62% possession, completed 84% of its passes, and recorded four shots. Those values alone do not establish whether the team is controlling the game, creating sustained pressure, becoming vulnerable to transitions, or merely accumulating low-value possession.

Different audiences also need different representations of the same match state:

- **Broadcasters and studio producers** need concise, timely, screen-ready narratives and machine-readable overlays.
- **Analysts** need detailed tactical context, metrics, event sequences, assumptions, and inspectable evidence.
- **Fans** need clear explanations and updates personalized by preferred team, player, language, or viewing mode.

MatchPulse addresses this gap by keeping the underlying match facts and evidence shared while adapting the interpretation and presentation to the audience. It must not publish unsupported match claims as facts.

## 3. Product promise

> One stream of football events becomes an explainable, verified story, then adapts into a broadcast overlay, an analyst breakdown, or a personalized fan update.

Every published insight should be traceable to a match state, a time window, supporting event IDs, relevant calculated metrics, and the validation decision that allowed it to be published. If the evidence is insufficient, MatchPulse should qualify the statement, use a deterministic fallback, or suppress the insight rather than fabricate certainty.

## 4. Background and motivation

The hackathon challenge asks participants to turn synthetic, football-realistic events into useful match intelligence, real-time narratives, automated recaps, and tailored experiences for fans, studios, broadcasters, and streaming platforms. Its stated pipeline includes ingesting events, interpreting them, explaining why moments matter, rendering them alongside a match, and personalizing the result.

The initial project strategy proposed starting with a synthetic-match simulator that streamed events into the backend. The project direction was subsequently refined: **build MatchPulse as a source-independent product first**. A simulator should not dictate the architecture or become the product's centerpiece. Small controlled fixtures are still necessary for unit and integration tests. After the actual product pipeline exists and is tested, choose the best additional data source and test scenarios based on observed gaps and competition rules.

This distinction matters because the core product logic should not depend on one particular simulator, provider, or dataset. The event ingestion layer is responsible for converting source-specific data into MatchPulse's canonical event representation.

## 5. Target users and use cases

### 5.1 Broadcaster / studio producer

Needs fast, accurate, concise context that can appear beside a live match. Example use case: the platform detects that Ridge United's pressure has risen over a rolling window and generates a compact overlay with the pressure change, relevant events, and a short explanation. Broadcast output should be structured and suitable for downstream graphical rendering.

### 5.2 Football analyst

Needs greater detail than a broadcast overlay: before-and-after metrics, relevant event sequences, tactical hypotheses, supporting and contradicting evidence, and access to agent reasoning artifacts in the form of structured findings and handoff status. Example use case: inspect whether a pressure swing corresponds to more high regains and attacking-third entries, rather than being caused by one isolated event.

### 5.3 Fan

Needs accessible, concise explanations and updates relevant to a chosen fictional or otherwise permitted team/player preference. Example use case: receive a plain-language update about why a team is under pressure, with optional preferred player/team and language settings.

### 5.4 Developer / evaluator / hackathon judge

Needs to inspect the actual architecture and verify that the multi-agent system is working. The interface should expose agent execution state, structured outputs, evidence checks, retries, fallbacks, latency, and trace information. The repository should explain how to reproduce the product and run the evaluation suite.

## 6. High-level goals

1. Ingest and normalize football match events through a source-independent event contract.
2. Maintain match state and calculate key metrics through deterministic, testable code.
3. Detect significant changes and meaningful moments based on documented rules and evidence.
4. Use distinct, purpose-specific agents to interpret match changes and generate narratives.
5. Validate factual and numerical claims before publishing an insight.
6. Provide bounded repair/retry and deterministic fallback behavior when agent outputs fail validation.
7. Present the same verified facts in genuinely different Fan, Analyst, and Broadcast experiences.
8. Make the system's evidence, agent coordination, and failure handling inspectable in the UI and logs.
9. Evaluate the product through reproducible tests, including quiet periods where no insight should be generated.
10. Deploy a working application on an appropriate Azure path and prepare a public repository plus a demonstration video of less than two minutes.
11. Preserve the ability to integrate a fuller synthetic generator, licensed dataset, or compatible live event source later without redesigning the intelligence engine.

## 7. Non-goals and explicit boundaries

- Do not make a synthetic match simulator the product's core architecture or the first major deliverable.
- Do not tightly couple metrics, agents, UI, or persistence to one dataset or provider.
- Do not ask an LLM to calculate authoritative numerical metrics such as possession percentages, event counts, or the project's pressure index. These belong in deterministic code.
- Do not publish unsupported AI claims silently. The application must be able to qualify, reject, repair, fall back, or suppress.
- Do not build a generic football chatbot as the core product.
- Do not build a statistics-only dashboard without explanations and personalization.
- Do not create several agents that merely duplicate the same summarization task. Each agent must have a defined contract and unique responsibility.
- Do not add Event Hubs, Azure Functions, or other infrastructure simply to increase the number of technologies shown. Add them only when the working core pipeline justifies them.
- Do not assume that public availability means data is licensed for this project or permitted in the final competition submission.
- Do not use actual Premier League branding, crests, match footage, or other third-party copyrighted material in the demo unless the project has the required rights. The conversation explicitly calls for fictional team names and custom visuals.

## 8. Competition-specific constraints from the conversation

The challenge description in the source conversation says the project must use synthetic, football-realistic data and that real Premier League match data is not redistributed to participants. The stated submission requirements include a public GitHub repository, a project pitch/description, and a public demo video that is less than two minutes long, shows the project running on its intended platform, and avoids unauthorized third-party trademarks or copyrighted material.

The conversation recorded a submission deadline of **October 27, 2026, at 11:59 PM Pacific Time**. Treat this as a deadline stated in the conversation, not as independently re-verified current competition information; check the official competition page before relying on it operationally.

## 9. Definition of success

MatchPulse is meaningfully successful when all of the following are demonstrable:

- A valid event submitted through the real API changes match state and produces deterministic metrics.
- A meaningful, event-supported match-state change can trigger analysis.
- The Match Analyst and Tactical Analyst provide distinct structured findings using the same versioned evidence window.
- The Narrative Producer generates audience-specific outputs from the shared findings.
- The Evidence Auditor / deterministic validator blocks invalid numerical claims and unsupported event references.
- A rejected story can be repaired at most the configured number of times, then falls back or is suppressed safely.
- Fan, Analyst, and Broadcast modes preserve the same verified facts while adapting presentation meaningfully.
- Users can inspect an insight's evidence, metric values, event IDs, validation status, and agent handoff history.
- Automated tests measure both positive behavior and restraint, including scenarios where no insight should be emitted.
- The application can be run or deployed reproducibly, and the final submission complies with the competition's data and media requirements.

## 10. Important context for coding agents

This document describes intended product behavior and decisions from the planning conversation, not proof that implementation exists. Before modifying code, inspect the actual repository, report what is already present, and align changes with the existing codebase. Do not assume that endpoints, modules, database collections, deployment configuration, or agent implementations described in the companion files already exist. Items explicitly labeled as proposed are scaffolding recommendations rather than established code.
