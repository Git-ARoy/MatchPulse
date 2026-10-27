"""End-to-end integration test verifying that MatchPulse ingests simulation events."""

from fastapi.testclient import TestClient

import app.main as matchpulse_main
from app.services.match_service import MatchService
from simulator.engine.match_sim import MatchSimulation


def test_simulation_to_matchpulse_pipeline():
    # Setup clean MatchPulse service
    matchpulse_main.service = MatchService()
    client = TestClient(matchpulse_main.app)

    sim_events = []
    sim = MatchSimulation(match_id="sim_integration_test", event_callback=sim_events.append)
    sim.start()

    # Step simulation
    for _ in range(50):
        sim.step(1.0)

    # Inject penalty
    sim.inject_penalty()
    sim.step(3.0)

    assert len(sim_events) >= 3

    # Ingest all simulation events into MatchPulse API
    for event in sim_events:
        res = client.post(f"/api/v1/matches/{event['match_id']}/events", json=event)
        assert res.status_code == 200, f"Failed on event: {event} -> {res.text}"
        body = res.json()
        assert body["accepted"] is True

    # Verify MatchPulse state
    state_res = client.get("/api/v1/matches/sim_integration_test/state")
    assert state_res.status_code == 200
    state = state_res.json()
    assert state["match_id"] == "sim_integration_test"
    assert len(state["teams"]) == 2

    # Verify that the new /api/v1/matches discovery endpoint lists this live simulation
    matches_res = client.get("/api/v1/matches")
    assert matches_res.status_code == 200
    items = matches_res.json()["items"]
    found = [m for m in items if m["match_id"] == "sim_integration_test"]
    assert len(found) == 1
    assert found[0]["event_count"] >= 3
