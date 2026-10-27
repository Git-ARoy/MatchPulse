"""Test simulator FastAPI app REST and status endpoints."""

from fastapi.testclient import TestClient
from simulator.app import app


def test_simulator_api_endpoints():
    client = TestClient(app)

    # 1. Matchups list
    matchups_res = client.get("/api/simulation/matchups")
    assert matchups_res.status_code == 200
    matchups = matchups_res.json()["items"]
    assert len(matchups) >= 3
    assert matchups[0]["id"] == "epl_mci_ars"

    # 2. Status
    status_res = client.get("/api/simulation/status")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert "snapshot" in status_data
    assert "dispatcher" in status_data

    # 3. Start, Pause, Resume, Speed
    start_res = client.post("/api/simulation/start")
    assert start_res.status_code == 200

    pause_res = client.post("/api/simulation/pause")
    assert pause_res.status_code == 200

    resume_res = client.post("/api/simulation/resume")
    assert resume_res.status_code == 200

    speed_res = client.post("/api/simulation/speed", json={"multiplier": 5.0})
    assert speed_res.status_code == 200
    assert speed_res.json()["speed_multiplier"] == 5.0

    # 4. Injections
    pen_res = client.post("/api/simulation/inject", json={"action": "penalty"})
    assert pen_res.status_code == 200

    fk_res = client.post("/api/simulation/inject", json={"action": "free_kick"})
    assert fk_res.status_code == 200

    red_res = client.post("/api/simulation/inject", json={"action": "red_card"})
    assert red_res.status_code == 200

    # 5. Tracking & Events
    track_res = client.get("/api/simulation/tracking")
    assert track_res.status_code == 200
    assert len(track_res.json()["home_team"]["players"]) == 11
    assert len(track_res.json()["away_team"]["players"]) == 11

    events_res = client.get("/api/simulation/events")
    assert events_res.status_code == 200
    assert len(events_res.json()["items"]) >= 1

    # 6. Reset
    reset_res = client.post("/api/simulation/reset", json={"matchup_id": "epl_liv_che"})
    assert reset_res.status_code == 200
    assert reset_res.json()["matchup_id"] == "epl_liv_che"
