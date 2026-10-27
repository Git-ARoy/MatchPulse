"""Simulation Bridge connecting MatchPulse directly to the physics-based match simulator.
Provides transparent fallback to an in-process simulation engine if the external
simulator container (port 8050) is offline.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import urllib.error
import urllib.request
from typing import Any

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore

from app.domain.events import CanonicalEvent
from app.services.match_service import MatchService

try:
    from simulator.engine.match_sim import MatchSimulation
    from simulator.engine.rosters import AVAILABLE_MATCHUPS
except ImportError:
    try:
        from app.simulator.engine.match_sim import MatchSimulation
        from app.simulator.engine.rosters import AVAILABLE_MATCHUPS
    except ImportError:
        MatchSimulation = None  # type: ignore
        AVAILABLE_MATCHUPS = []  # type: ignore

logger = logging.getLogger("matchpulse.simulation_bridge")


class SimulationBridge:
    def __init__(self, match_service: MatchService) -> None:
        self.match_service = match_service
        self.external_url = os.getenv("SIMULATOR_API_URL", "http://localhost:8050").rstrip("/")
        self._in_process_sim: MatchSimulation | None = None
        self._in_process_task: asyncio.Task | None = None
        self._in_process_lock = asyncio.Lock()
        self._external_available: bool = False
        self._last_check_time: float = 0.0

    def _get_or_create_local_sim(self, match_id: str = "synthetic_ridge_harbor", matchup_id: str = "synthetic_ridge_harbor") -> MatchSimulation | None:
        if MatchSimulation is None:
            return None
        if self._in_process_sim is None or self._in_process_sim.match_id != match_id:
            def on_event(ev: dict[str, Any]) -> None:
                try:
                    canon = CanonicalEvent.model_validate(ev)
                    self.match_service.ingest(canon)
                except Exception as ex:
                    logger.debug("Ingestion from simulator: %s", ex)

            self._in_process_sim = MatchSimulation(
                match_id=match_id,
                matchup_id=matchup_id,
                event_callback=on_event,
            )
        return self._in_process_sim

    async def _http_get(self, url: str, timeout: float = 1.0) -> dict[str, Any] | None:
        if httpx is not None:
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    res = await client.get(url)
                    if res.status_code == 200:
                        return res.json()
            except Exception:
                return None
        else:
            def _sync_get() -> dict[str, Any] | None:
                req = urllib.request.Request(url, headers={"User-Agent": "MatchPulse"})
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    if resp.status == 200:
                        return json.loads(resp.read().decode())
                return None
            try:
                return await asyncio.to_thread(_sync_get)
            except Exception:
                return None
        return None

    async def _http_post(self, url: str, payload: dict[str, Any] | None = None, timeout: float = 1.0) -> dict[str, Any] | None:
        if httpx is not None:
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    res = await client.post(url, json=payload or {})
                    if res.status_code == 200:
                        return res.json()
            except Exception:
                return None
        else:
            def _sync_post() -> dict[str, Any] | None:
                data = json.dumps(payload or {}).encode("utf-8")
                req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json", "User-Agent": "MatchPulse"}, method="POST")
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    if resp.status == 200:
                        return json.loads(resp.read().decode())
                return None
            try:
                return await asyncio.to_thread(_sync_post)
            except Exception:
                return None
        return None

    async def _check_external(self) -> bool:
        """Probe external simulator service."""
        res = await self._http_get(f"{self.external_url}/api/simulation/status", timeout=0.6)
        self._external_available = bool(res)
        return self._external_available

    async def _run_local_tick_loop(self) -> None:
        """In-process simulation tick loop (100ms interval = 10Hz)."""
        tick_interval = 0.1
        sim = self._get_or_create_local_sim()
        if not sim:
            return
        while True:
            try:
                if not sim.is_paused:
                    sim.step(tick_interval)
            except asyncio.CancelledError:
                break
            except Exception as ex:
                logger.error("Simulation loop error: %s", ex)
            await asyncio.sleep(tick_interval)

    async def get_status(self, match_id: str = "synthetic_ridge_harbor") -> dict[str, Any]:
        if await self._check_external():
            data = await self._http_get(f"{self.external_url}/api/simulation/status", timeout=1.0)
            if data:
                data["mode"] = "external_service"
                data["connected"] = True
                return data

        sim = self._get_or_create_local_sim(match_id)
        if not sim:
            return {
                "mode": "standby",
                "connected": True,
                "snapshot": {"match_id": match_id, "is_paused": True, "phase": "ready", "minute": 0, "second": 0, "event_counter": 0},
                "recent_events": [],
                "dispatcher": {"status": "standby", "target_api_url": "internal"},
            }
        return {
            "mode": "in_process_engine",
            "connected": True,
            "snapshot": sim.get_snapshot(),
            "recent_events": sim.recent_events[-15:],
            "dispatcher": {
                "target_api_url": "internal",
                "status": "connected",
                "total_dispatched": sim.event_counter,
                "delivered_count": sim.event_counter,
            },
        }

    async def start(self, match_id: str = "synthetic_ridge_harbor") -> dict[str, Any]:
        if await self._check_external():
            res = await self._http_post(f"{self.external_url}/api/simulation/start")
            if res:
                return res

        sim = self._get_or_create_local_sim(match_id)
        sim.start()
        if self._in_process_task is None or self._in_process_task.done():
            self._in_process_task = asyncio.create_task(self._run_local_tick_loop())
        return {"status": "started", "phase": sim.phase.value, "match_id": sim.match_id}

    async def pause(self) -> dict[str, Any]:
        if await self._check_external():
            res = await self._http_post(f"{self.external_url}/api/simulation/pause")
            if res:
                return res

        if self._in_process_sim:
            self._in_process_sim.pause()
        return {"status": "paused"}

    async def resume(self) -> dict[str, Any]:
        if await self._check_external():
            res = await self._http_post(f"{self.external_url}/api/simulation/resume")
            if res:
                return res

        if self._in_process_sim:
            self._in_process_sim.resume()
            if self._in_process_task is None or self._in_process_task.done():
                self._in_process_task = asyncio.create_task(self._run_local_tick_loop())
        return {"status": "resumed"}

    async def set_speed(self, multiplier: float) -> dict[str, Any]:
        if await self._check_external():
            res = await self._http_post(f"{self.external_url}/api/simulation/speed", payload={"multiplier": multiplier})
            if res:
                return res

        if self._in_process_sim:
            self._in_process_sim.set_speed(multiplier)
            return {"status": "ok", "speed_multiplier": self._in_process_sim.speed_multiplier}
        return {"status": "ok", "speed_multiplier": multiplier}

    async def reset(self, matchup_id: str | None = None) -> dict[str, Any]:
        if await self._check_external():
            res = await self._http_post(f"{self.external_url}/api/simulation/reset", payload={"matchup_id": matchup_id})
            if res:
                return res

        target_id = matchup_id or "synthetic_ridge_harbor"
        if self._in_process_sim:
            self._in_process_sim.reset(matchup_id=target_id)
        else:
            self._get_or_create_local_sim(target_id, target_id)
        return {"status": "reset", "matchup_id": target_id}

    async def inject(self, action: str, team_id: str | None = None) -> dict[str, Any]:
        if await self._check_external():
            res = await self._http_post(f"{self.external_url}/api/simulation/inject", payload={"action": action, "team_id": team_id})
            if res:
                return res

        if not self._in_process_sim:
            self._get_or_create_local_sim()
        sim = self._in_process_sim
        if not sim:
            return {"status": "error", "message": "Simulation not initialized"}

        if action == "penalty":
            sim.inject_penalty(team_id)
        elif action == "red_card":
            sim.inject_red_card(team_id)
        elif action == "free_kick":
            sim.inject_free_kick(team_id)
        else:
            return {"status": "error", "message": f"Unknown action: {action}"}
        return {"status": "injected", "action": action}

    async def get_tracking(self, match_id: str) -> dict[str, Any] | None:
        if await self._check_external():
            data = await self._http_get(f"{self.external_url}/api/simulation/tracking")
            if data and data.get("match_id") == match_id:
                return data

        sim = self._get_or_create_local_sim(match_id)
        if sim:
            return sim.get_snapshot()
        return None

    def list_matchups(self) -> list[dict[str, Any]]:
        return [
            {
                "id": m["id"],
                "title": m["title"],
                "home": m["home"],
                "away": m["away"],
            }
            for m in AVAILABLE_MATCHUPS
        ]
