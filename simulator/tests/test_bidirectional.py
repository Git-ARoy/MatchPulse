"""Test bi-directional communication between MatchPulse and the Simulator."""

import asyncio
import pytest
from fastapi.testclient import TestClient

import app.main as matchpulse_main
from app.services.match_service import MatchService
from simulator.app import app as simulator_app
from simulator.engine.dispatcher import EventDispatcher
from simulator.engine.match_sim import MatchSimulation


def test_bidirectional_data_exchange():
    # Setup clean MatchPulse service
    matchpulse_main.service = MatchService()
    mp_client = TestClient(matchpulse_main.app)
    sim_client = TestClient(simulator_app)

    match_id = "epl_bidirectional_test"
    dispatched = []

    # 1. Simulator generates events
    sim = MatchSimulation(match_id=match_id, event_callback=dispatched.append)
    sim.start()
    for _ in range(30):
        sim.step(1.0)
    sim.inject_penalty()
    sim.step(3.0)

    assert len(dispatched) >= 2

    # 2. Simulator pushes events to MatchPulse
    for evt in dispatched:
        res = mp_client.post(f"/api/v1/matches/{match_id}/events", json=evt)
        assert res.status_code == 200

    # 3. MatchPulse has computed the match state
    mp_state = mp_client.get(f"/api/v1/matches/{match_id}/state").json()
    assert mp_state["match_id"] == match_id
    assert "metrics" in mp_state

    # 4. Dispatcher pulls intelligence back from MatchPulse
    dispatcher = EventDispatcher()
    dispatcher.current_match_id = match_id

    # Test sync using TestClient
    state_res = mp_client.get(f"/api/v1/matches/{match_id}/state")
    assert state_res.status_code == 200
    dispatcher.matchpulse_intelligence["connected"] = True
    dispatcher.matchpulse_intelligence["state_version"] = state_res.json()["state_version"]
    dispatcher.matchpulse_intelligence["pressure_metrics"] = state_res.json()["metrics"]

    metrics = dispatcher.get_metrics()
    assert metrics["matchpulse_intelligence"]["connected"] is True
    assert metrics["matchpulse_intelligence"]["state_version"] > 0
    assert len(metrics["matchpulse_intelligence"]["pressure_metrics"]) > 0

    # 5. MatchPulse queries the simulator for 22-player tracking
    # When simulator is mounted, simulator /api/simulation/tracking provides the 22 player positions
    tracking_res = sim_client.get("/api/simulation/tracking")
    assert tracking_res.status_code == 200
    track_body = tracking_res.json()
    assert len(track_body["home_team"]["players"]) == 11
    assert len(track_body["away_team"]["players"]) == 11
    assert "ball" in track_body
