"""API-level tests for the synthetic, source-independent first vertical slice."""

import pytest
import json
from fastapi.testclient import TestClient

import app.main as main
from app.services.match_service import MatchService
from app.services.insight_generator import InsightGenerator


@pytest.fixture()
def client():
    main.service = MatchService()
    return TestClient(main.app)


def payload(event_id: str, minute: int, event_type: str = "pass", team_id: str = "ridge_united", **extra):
    attributes = extra.pop("attributes", {"completed": True} if event_type == "pass" else {})
    return {
        "event_id": event_id,
        "match_id": "sim_match_001",
        "minute": minute,
        "second": extra.pop("second", 0),
        "event_type": event_type,
        "team_id": team_id,
        "attributes": attributes,
        **extra,
    }


def test_health_and_valid_event_contract(client):
    assert client.get("/api/v1/health").json()["status"] == "ok"
    response = client.post("/api/v1/matches/sim_match_001/events", json=payload("evt_1", 1, x=70, y=30))
    assert response.status_code == 200
    body = response.json()
    assert body["accepted"] is True
    assert body["processing_status"] == "processed"
    assert body["match_state_version"] == 1
    state = client.get("/api/v1/matches/sim_match_001/state").json()
    assert state["teams"]["ridge_united"]["passes_completed"] == 1
    assert state["metrics"]["pressure_index:ridge_united"]["definition_version"] == "pressure-v1"


def test_api_returns_structured_error_for_unknown_or_missing_fields(client):
    invalid = payload("evt_1", 1, "not_a_real_event")
    response = client.post("/api/v1/matches/sim_match_001/events", json=invalid)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    missing = payload("evt_2", 1)
    del missing["team_id"]
    response = client.post("/api/v1/matches/sim_match_001/events", json=missing)
    assert response.status_code == 422
    assert response.json()["error"]["details"]


def test_duplicate_is_idempotent_but_conflicting_duplicate_is_rejected(client):
    original = payload("evt_1", 1)
    assert client.post("/api/v1/matches/sim_match_001/events", json=original).status_code == 200
    duplicate = client.post("/api/v1/matches/sim_match_001/events", json=original)
    assert duplicate.status_code == 200
    assert duplicate.json()["duplicate"] is True
    conflict = client.post("/api/v1/matches/sim_match_001/events", json=payload("evt_1", 2))
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "EVENT_CONFLICT"


def test_out_of_order_event_is_explicitly_rejected(client):
    assert client.post("/api/v1/matches/sim_match_001/events", json=payload("evt_2", 10)).status_code == 200
    response = client.post("/api/v1/matches/sim_match_001/events", json=payload("evt_1", 9))
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "EVENT_OUT_OF_ORDER"


def test_pressure_shift_creates_insight_linked_to_exact_source_events(client):
    # Controlled synthetic fixture: a low-pressure previous window followed by
    # a 40-point pressure-v1 window (high regain + attacking-third entry).
    events = [
        payload("evt_old", 1),
        payload("evt_regain", 8, "high_regain"),
        payload("evt_entry", 8, "attacking_third_entry", second=10),
    ]
    for item in events:
        response = client.post("/api/v1/matches/sim_match_001/events", json=item)
        assert response.status_code == 200
        last_response = response.json()
    listed = client.get("/api/v1/matches/sim_match_001/insights")
    assert listed.status_code == 200
    insight = listed.json()["items"][0]
    assert insight["insight_type"] == "pressure_shift"
    assert insight["validation"]["status"] == "approved"
    evidence = client.get(f"/api/v1/insights/{insight['insight_id']}/evidence").json()
    assert evidence["event_ids"] == ["evt_regain", "evt_entry"]
    assert insight["source_event_ids"] == evidence["event_ids"]
    assert evidence["metrics"][0]["name"] == "pressure_index"
    assert evidence["metrics"][0]["value"] == 40.0
    stages = [item["stage"] for item in insight["agent_findings"]]
    assert stages == ["match_analyst", "tactical_analyst", "narrative_producer", "evidence_auditor"]
    trace = client.get(f"/api/v1/analysis-runs/{last_response['analysis_run_ids'][0]}/trace")
    assert trace.status_code == 200
    assert trace.json()["outcome"] == "insight_published"


def test_quiet_period_does_not_publish_an_insight(client):
    for minute in (1, 2, 3):
        response = client.post("/api/v1/matches/sim_match_001/events", json=payload(f"evt_{minute}", minute))
        assert response.status_code == 200
        assert response.json()["published_insight_ids"] == []
    assert client.get("/api/v1/matches/sim_match_001/insights").json()["items"] == []


def test_event_ledger_endpoint_is_ordered_and_ticker_ready(client):
    for event in [payload("evt_one", 3, player_id="ridge_08"), payload("evt_two", 3, "tackle", second=10, player_id="ridge_06")]:
        assert client.post("/api/v1/matches/sim_match_001/events", json=event).status_code == 200
    response = client.get("/api/v1/matches/sim_match_001/events?limit=1")
    assert response.status_code == 200
    assert response.json()["items"][0]["event_id"] == "evt_one"
    cursor = response.json()["next_cursor"]
    assert client.get(f"/api/v1/matches/sim_match_001/events?after={cursor}").json()["items"][0]["event_id"] == "evt_two"


def test_dev_pressure_fixture_uses_real_ingestion_and_exposes_variants(client):
    response = client.post("/api/v1/dev/matches/demo_pressure/fixtures/pressure-swing")
    assert response.status_code == 200
    body = response.json()
    assert body["accepted_count"] == 3
    assert len(body["published_insight_ids"]) == 1
    events = client.get("/api/v1/matches/demo_pressure/events").json()["items"]
    assert [item["event_id"] for item in events] == [
        "fixture_pressure_swing_1", "fixture_pressure_swing_2", "fixture_pressure_swing_3",
    ]
    insight = client.get("/api/v1/matches/demo_pressure/insights").json()["items"][0]
    assert set(insight["audience_variants"]) == {"fan", "analyst", "broadcast"}
    assert client.post("/api/v1/dev/matches/demo_pressure/fixtures/quiet-period").status_code == 409


def test_unknown_dev_fixture_is_a_structured_not_found(client):
    response = client.post("/api/v1/dev/matches/demo_unknown/fixtures/not-real")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "FIXTURE_NOT_FOUND"


def test_a_rejected_candidate_gets_one_evidence_locked_repair(client, monkeypatch):
    original_generate = InsightGenerator.generate
    calls = 0

    def flaky_generate(self, *args, **kwargs):
        nonlocal calls
        calls += 1
        insight = original_generate(self, *args, **kwargs)
        if calls == 1:
            return insight.model_copy(update={"source_event_ids": ["unverified_event"]})
        return insight

    monkeypatch.setattr(InsightGenerator, "generate", flaky_generate)
    for event in [payload("repair_old", 1), payload("repair_regain", 8, "high_regain"), payload("repair_entry", 8, "attacking_third_entry", second=10)]:
        assert client.post("/api/v1/matches/sim_match_001/events", json=event).status_code == 200
    insight = client.get("/api/v1/matches/sim_match_001/insights").json()["items"][0]
    assert insight["validation"]["status"] == "repaired"
    assert insight["validation"]["repair_count"] == 1
    stages = [stage["stage"] for stage in insight["agent_findings"]]
    assert stages.count("narrative_producer") == 2


def test_live_stream_pushes_committed_transition(client):
    with client.websocket_connect("/api/v1/matches/live_match/live-stream") as websocket:
        assert websocket.receive_json()["type"] == "match.awaiting_events"
        response = client.post("/api/v1/matches/live_match/events", json={**payload("live_1", 1), "match_id": "live_match"})
        assert response.status_code == 200
        update = websocket.receive_json()
        assert update["type"] == "match.transition"
        assert update["event"]["event_id"] == "live_1"
        assert update["state"]["state_version"] == 1


def test_statsbomb_import_marks_completed_match_as_not_live(client, tmp_path, monkeypatch):
    events_dir = tmp_path / "data" / "events"
    events_dir.mkdir(parents=True)
    (events_dir / "77.json").write_text(json.dumps([{
        "id": "sb-1", "minute": 2, "second": 3,
        "type": {"name": "Pass"}, "team": {"id": 1}, "player": {"id": 9},
        "location": [72, 40], "pass": {},
    }]))
    monkeypatch.setenv("STATSBOMB_OPEN_DATA_ROOT", str(tmp_path))
    response = client.post("/api/v1/import/statsbomb/77")
    assert response.status_code == 200
    assert response.json()["historical"] is True
    state = client.get("/api/v1/matches/statsbomb_77/state").json()
    assert state["data_source"] == "statsbomb-open-data"
    assert state["live_feed_available"] is False
    assert state["historical"] is True


def test_statsbomb_match_discovery_lists_importable_matches(client, tmp_path, monkeypatch):
    matches = tmp_path / "data" / "matches" / "1"
    events = tmp_path / "data" / "events"
    matches.mkdir(parents=True)
    events.mkdir(parents=True)
    (matches / "2.json").write_text(json.dumps([{
        "match_id": 77,
        "match_date": "2020-01-01",
        "home_team": {"home_team_name": "Ridge United"},
        "away_team": {"away_team_name": "Harbor FC"},
        "competition": {"competition_name": "Demo League"},
        "season": {"season_name": "2020/21"},
    }]))
    (events / "77.json").write_text("[]")
    monkeypatch.setenv("STATSBOMB_OPEN_DATA_ROOT", str(tmp_path))
    response = client.get("/api/v1/import/statsbomb/matches?competition_id=1&season_id=2")
    assert response.status_code == 200
    assert response.json()["items"][0]["source_match_id"] == "77"
    assert response.json()["live_feed_available"] is False


def test_synthetic_showcase_runs_the_real_pipeline_and_exposes_a_recap(client):
    response = client.post("/api/v1/demo/scenarios/momentum-surge")
    assert response.status_code == 200
    body = response.json()
    assert body["synthetic"] is True
    assert body["accepted_count"] == 10
    assert body["published_insight_ids"]

    state = client.get("/api/v1/matches/synthetic_ridge_harbor/state").json()
    assert state["synthetic"] is True
    assert state["teams"]["ridge_united"]["goals"] == 1
    assert state["team_metrics"]["ridge_united"]["average_pass_distance_m"] is not None
    assert state["players"]

    recap = client.get("/api/v1/matches/synthetic_ridge_harbor/recap?audience=broadcast&language=es")
    assert recap.status_code == 200
    assert recap.json()["synthetic"] is True
    assert recap.json()["language"] == "es"


def test_synthetic_scenario_catalog_is_explicitly_fictional(client):
    response = client.get("/api/v1/demo/scenarios")
    assert response.status_code == 200
    assert response.json()["items"][0]["match_id"].startswith("synthetic_")
    assert "No real Premier League" in response.json()["data_policy"]
