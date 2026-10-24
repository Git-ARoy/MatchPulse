"""Optional Microsoft Foundry narrative provider.

This adapter is intentionally narrow: it receives the immutable evidence
context and may propose wording only. It has no access to the event ledger or
metric calculations, and callers must validate its candidate before publishing.
"""

from __future__ import annotations

import json
import os
import re
import asyncio

from app.agents.contracts import EvidenceContext, NarrativeOutput


class FoundryUnavailableError(RuntimeError):
    """Foundry is requested but cannot be safely used in this environment."""


class FoundryNarrativeProducer:
    """Create one short-lived Foundry-backed MAF agent per analysis run."""

    _BLOCKED_INTERPRETATIONS = re.compile(
        r"\b(formation|pressing scheme|man[- ]marking|tactical intent|because|caused by)\b",
        re.IGNORECASE,
    )

    def __init__(self, project_endpoint: str, model: str) -> None:
        self.project_endpoint = project_endpoint
        self.model = model

    @classmethod
    def from_environment(cls) -> "FoundryNarrativeProducer | None":
        if os.getenv("MATCHPULSE_NARRATIVE_PROVIDER", "deterministic").lower() != "foundry":
            return None
        endpoint = os.getenv("FOUNDRY_PROJECT_ENDPOINT", "").strip()
        model = os.getenv("FOUNDRY_MODEL", "").strip()
        if not endpoint or not model:
            raise FoundryUnavailableError(
                "MATCHPULSE_NARRATIVE_PROVIDER=foundry requires FOUNDRY_PROJECT_ENDPOINT and FOUNDRY_MODEL."
            )
        return cls(endpoint, model)

    async def produce(self, context: EvidenceContext) -> NarrativeOutput:
        """Request structured wording from Foundry using Azure CLI identity.

        Imports are local so the default deterministic API installation stays
        usable without Foundry dependencies or credentials.
        """
        try:
            from agent_framework import Agent
            from agent_framework.foundry import FoundryChatClient
            from azure.identity import DefaultAzureCredential
        except ImportError as error:
            raise FoundryUnavailableError(
                "Foundry support is optional. Install `pip install -e '.[foundry]'` before selecting it."
            ) from error

        facts = context.model_dump(mode="json")
        prompt = (
            "Write a concise football insight using ONLY these immutable facts. "
            "Do not calculate, add numbers, name events that are not listed, or claim a tactical cause. "
            "Return JSON only with headline, summary, what_changed, and why_it_matters. "
            f"Facts: {json.dumps(facts, sort_keys=True)}"
        )
        try:
            client = FoundryChatClient(
                project_endpoint=self.project_endpoint,
                model=self.model,
                credential=DefaultAzureCredential(exclude_interactive_browser_credential=True),
            )
            agent = Agent(client, name="matchpulse_foundry_narrative", instructions=(
                "You are MatchPulse's Narrative Producer. Follow the request exactly; "
                "evidence and calculations are not yours to change."
            ))
            response = await asyncio.wait_for(agent.run(prompt), timeout=0.8)
            output = NarrativeOutput.model_validate(json.loads(response.text))
        except FoundryUnavailableError:
            raise
        except TimeoutError as error:
            raise FoundryUnavailableError("Foundry inference exceeded the 800 ms circuit-breaker budget.") from error
        except Exception as error:
            raise FoundryUnavailableError(f"Foundry narrative request failed: {error}") from error
        self._validate_conservative_copy(output)
        return output

    def _validate_conservative_copy(self, output: NarrativeOutput) -> None:
        """Reject wording likely to contain new measured or tactical claims."""
        values = (output.headline, output.summary, output.what_changed, output.why_it_matters)
        if any(not value.strip() or len(value) > 500 for value in values):
            raise FoundryUnavailableError("Foundry returned an empty or oversized narrative field.")
        if any(re.search(r"\d", value) for value in values):
            raise FoundryUnavailableError("Foundry narrative contains a numerical claim outside the locked evidence rendering.")
        if any(self._BLOCKED_INTERPRETATIONS.search(value) for value in values):
            raise FoundryUnavailableError("Foundry narrative contains a tactical-causality claim outside available evidence.")
