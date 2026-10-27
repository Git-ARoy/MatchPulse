"""FastAPI server for the MatchPulse Standalone Synthetic Match Simulator."""

from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from simulator.engine.dispatcher import EventDispatcher
from simulator.engine.match_sim import MatchSimulation
from simulator.engine.rosters import AVAILABLE_MATCHUPS

# Configuration
SIMULATOR_PORT = int(os.getenv("SIMULATOR_PORT", "8050"))
MATCHPULSE_API_URL = os.getenv("MATCHPULSE_API_URL", "http://localhost:8000")

dispatcher = EventDispatcher(target_api_url=MATCHPULSE_API_URL)


def on_simulation_event(event: dict[str, Any]) -> None:
    """Callback triggered whenever MatchSimulation emits a canonical event."""
    dispatcher.enqueue(event)


simulation = MatchSimulation(
    match_id="epl_mci_ars",
    matchup_id="epl_mci_ars",
    event_callback=on_simulation_event,
)

connected_websockets: set[WebSocket] = set()
sim_loop_task: asyncio.Task | None = None


async def simulation_tick_loop() -> None:
    """Master simulation loop running at 10 Hz (every 100ms)."""
    tick_interval = 0.1  # 100ms
    while True:
        try:
            simulation.step(tick_interval)
            snapshot = simulation.get_snapshot()

            # Broadcast to active WebSockets
            if connected_websockets:
                payload = {
                    "type": "simulation.tick",
                    "snapshot": snapshot,
                    "dispatcher": dispatcher.get_metrics(),
                    "recent_events": simulation.recent_events[-15:],
                }
                dead_sockets = []
                for ws in connected_websockets:
                    try:
                        await ws.send_json(payload)
                    except Exception:
                        dead_sockets.append(ws)
                for dead in dead_sockets:
                    connected_websockets.discard(dead)

        except asyncio.CancelledError:
            break
        except Exception as ex:
            print(f"[SimLoop Error] {ex}")

        await asyncio.sleep(tick_interval)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global sim_loop_task
    dispatcher.start()
    sim_loop_task = asyncio.create_task(simulation_tick_loop())
    yield
    if sim_loop_task:
        sim_loop_task.cancel()
        try:
            await sim_loop_task
        except asyncio.CancelledError:
            pass
    await dispatcher.stop()


app = FastAPI(
    title="MatchPulse Synthetic Match Simulator",
    description="Standalone 90-minute real-time Premier League match simulation engine",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request schemas
class SpeedRequest(BaseModel):
    multiplier: float = Field(..., ge=0.5, le=120.0)


class ResetRequest(BaseModel):
    matchup_id: str | None = None


class InjectRequest(BaseModel):
    action: str  # penalty | red_card | free_kick
    team_id: str | None = None


# Endpoints
@app.get("/api/simulation/status")
def get_status() -> dict[str, Any]:
    return {
        "snapshot": simulation.get_snapshot(),
        "dispatcher": dispatcher.get_metrics(),
        "recent_events": simulation.recent_events[-20:],
    }


@app.get("/api/simulation/matchups")
def list_matchups() -> dict[str, Any]:
    return {
        "items": [
            {
                "id": m["id"],
                "title": m["title"],
                "home": m["home"],
                "away": m["away"],
            }
            for m in AVAILABLE_MATCHUPS
        ],
        "active_matchup_id": simulation.matchup_id,
    }


@app.post("/api/simulation/start")
def start_simulation() -> dict[str, str]:
    simulation.start()
    return {"status": "started", "phase": simulation.phase.value}


@app.post("/api/simulation/pause")
def pause_simulation() -> dict[str, str]:
    simulation.pause()
    return {"status": "paused"}


@app.post("/api/simulation/resume")
def resume_simulation() -> dict[str, str]:
    simulation.resume()
    return {"status": "resumed"}


@app.post("/api/simulation/reset")
def reset_simulation(body: ResetRequest | None = None) -> dict[str, str]:
    matchup_id = body.matchup_id if body else None
    simulation.reset(matchup_id=matchup_id)
    return {"status": "reset", "matchup_id": simulation.matchup_id}


@app.post("/api/simulation/advance-half")
def advance_half() -> dict[str, str]:
    simulation.advance_half_time()
    return {"status": "advanced", "phase": simulation.phase.value}


@app.post("/api/simulation/speed")
def set_speed(body: SpeedRequest) -> dict[str, Any]:
    simulation.set_speed(body.multiplier)
    return {"status": "ok", "speed_multiplier": simulation.speed_multiplier}


@app.post("/api/simulation/inject")
def inject_scenario(body: InjectRequest) -> dict[str, str]:
    if body.action == "penalty":
        simulation.inject_penalty(body.team_id)
    elif body.action == "red_card":
        simulation.inject_red_card(body.team_id)
    elif body.action == "free_kick":
        simulation.inject_free_kick(body.team_id)
    else:
        return {"status": "error", "message": f"Unknown action: {body.action}"}
    return {"status": "injected", "action": body.action}


@app.get("/api/simulation/tracking")
def get_tracking() -> dict[str, Any]:
    return simulation.get_snapshot()


@app.get("/api/simulation/events")
def get_events() -> dict[str, Any]:
    return {"items": simulation.recent_events}


@app.websocket("/ws/live")
async def live_websocket(websocket: WebSocket) -> None:
    await websocket.accept()
    connected_websockets.add(websocket)
    try:
        # Send initial snapshot immediately
        await websocket.send_json({
            "type": "simulation.snapshot",
            "snapshot": simulation.get_snapshot(),
            "dispatcher": dispatcher.get_metrics(),
            "recent_events": simulation.recent_events[-15:],
        })
        while True:
            # Keep alive read loop
            _ = await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        connected_websockets.discard(websocket)


# Mount static web UI files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/")
    def serve_index() -> FileResponse:
        return FileResponse(os.path.join(static_dir, "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("simulator.app:app", host="0.0.0.0", port=SIMULATOR_PORT, reload=False)
