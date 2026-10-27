"""Bi-directional dispatcher streaming canonical events to MatchPulse and pulling
live AI intelligence, pressure metrics, and audit findings back into the model.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Any

import httpx

logger = logging.getLogger("simulator.dispatcher")


class EventDispatcher:
    """Queues canonical events and pushes them to MatchPulse's HTTP ingestion gateway,
    while continuously receiving analyzed intelligence back from MatchPulse.
    """

    def __init__(self, target_api_url: str | None = None) -> None:
        self.target_api_url = (target_api_url or os.getenv("MATCHPULSE_API_URL", "http://localhost:8000")).rstrip("/")
        self.queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=1000)
        self.worker_task: asyncio.Task | None = None
        self.pull_task: asyncio.Task | None = None
        self.is_running = False

        # Metrics & Telemetry
        self.total_dispatched = 0
        self.total_delivered_200 = 0
        self.total_conflicts = 0
        self.total_failed = 0
        self.last_status: str = "idle"
        self.last_latency_ms: float = 0.0
        self.last_error: str | None = None
        self.current_match_id: str = "epl_mci_ars"

        # Bi-directional MatchPulse Intelligence Data
        self.matchpulse_intelligence: dict[str, Any] = {
            "connected": False,
            "state_version": 0,
            "pressure_metrics": {},
            "team_metrics": {},
            "latest_insights": [],
            "last_synced_at": None,
        }

    def start(self) -> None:
        if self.worker_task is None or self.worker_task.done():
            self.is_running = True
            self.worker_task = asyncio.create_task(self._dispatch_loop())
            self.pull_task = asyncio.create_task(self._intelligence_sync_loop())
            logger.info("Bi-directional dispatcher started targeting %s", self.target_api_url)

    async def stop(self) -> None:
        self.is_running = False
        for task in (self.worker_task, self.pull_task):
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        self.worker_task = None
        self.pull_task = None

    def enqueue(self, event: dict[str, Any]) -> None:
        """Enqueue an event non-blockingly."""
        self.total_dispatched += 1
        self.current_match_id = event.get("match_id", self.current_match_id)
        try:
            self.queue.put_nowait(event)
        except asyncio.QueueFull:
            # Drop oldest if congested
            try:
                self.queue.get_nowait()
            except Exception:
                pass
            self.queue.put_nowait(event)

    async def _dispatch_loop(self) -> None:
        """Pushes events from the model to MatchPulse."""
        async with httpx.AsyncClient(timeout=3.0) as client:
            while self.is_running:
                try:
                    event = await self.queue.get()
                except asyncio.CancelledError:
                    break

                match_id = event.get("match_id", "default_match")
                self.current_match_id = match_id
                endpoint = f"{self.target_api_url}/api/v1/matches/{match_id}/events"

                start_time = time.perf_counter()
                try:
                    response = await client.post(endpoint, json=event)
                    latency = (time.perf_counter() - start_time) * 1000.0
                    self.last_latency_ms = round(latency, 1)

                    if response.status_code == 200:
                        self.total_delivered_200 += 1
                        self.last_status = "connected"
                        self.last_error = None
                        # Immediately schedule a quick pull on accepted events
                        asyncio.create_task(self._fetch_matchpulse_data(client, match_id))
                    elif response.status_code in (409, 422):
                        self.total_conflicts += 1
                        self.last_status = f"warning_{response.status_code}"
                        self.last_error = response.text[:120]
                    else:
                        self.total_failed += 1
                        self.last_status = f"error_{response.status_code}"
                        self.last_error = response.text[:120]
                except Exception as ex:
                    self.total_failed += 1
                    self.last_status = "unreachable"
                    self.last_error = str(ex)

                self.queue.task_done()

    async def _intelligence_sync_loop(self) -> None:
        """Periodically pulls live analytics, pressure index, and insights from MatchPulse back to the model."""
        async with httpx.AsyncClient(timeout=3.0) as client:
            while self.is_running:
                try:
                    await self._fetch_matchpulse_data(client, self.current_match_id)
                except asyncio.CancelledError:
                    break
                except Exception:
                    pass
                await asyncio.sleep(2.0)

    async def _fetch_matchpulse_data(self, client: httpx.AsyncClient, match_id: str) -> None:
        """Query MatchPulse state and insights for the active match."""
        try:
            state_url = f"{self.target_api_url}/api/v1/matches/{match_id}/state"
            insights_url = f"{self.target_api_url}/api/v1/matches/{match_id}/insights?limit=5"

            state_res, insights_res = await asyncio.gather(
                client.get(state_url),
                client.get(insights_url),
                return_exceptions=True,
            )

            if isinstance(state_res, httpx.Response) and state_res.status_code == 200:
                state_data = state_res.json()
                self.matchpulse_intelligence["connected"] = True
                self.matchpulse_intelligence["state_version"] = state_data.get("state_version", 0)
                self.matchpulse_intelligence["pressure_metrics"] = state_data.get("metrics", {})
                self.matchpulse_intelligence["team_metrics"] = state_data.get("team_metrics", {})
                self.matchpulse_intelligence["last_synced_at"] = time.strftime("%H:%M:%S")

            if isinstance(insights_res, httpx.Response) and insights_res.status_code == 200:
                insights_data = insights_res.json()
                self.matchpulse_intelligence["latest_insights"] = [
                    {
                        "insight_id": item.get("insight_id"),
                        "headline": item.get("headline"),
                        "summary": item.get("summary"),
                        "why_it_matters": item.get("why_it_matters"),
                        "clock": f"{item.get('match_clock', {}).get('minute', 0)}:{item.get('match_clock', {}).get('second', 0):02d}",
                        "validation_status": item.get("validation", {}).get("status", "verified") if item.get("validation") else "verified",
                    }
                    for item in insights_data.get("items", [])
                ]
        except Exception:
            pass

    def get_metrics(self) -> dict[str, Any]:
        return {
            "target_api_url": self.target_api_url,
            "status": self.last_status,
            "total_dispatched": self.total_dispatched,
            "delivered_count": self.total_delivered_200,
            "conflict_count": self.total_conflicts,
            "error_count": self.total_failed,
            "latency_ms": self.last_latency_ms,
            "last_error": self.last_error,
            "queue_pending": self.queue.qsize(),
            "matchpulse_intelligence": self.matchpulse_intelligence,
        }
