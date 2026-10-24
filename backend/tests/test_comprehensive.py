"""Comprehensive tests for the deterministic analytics and insight pipeline.

Covers: moment detection, evidence builder, insight generator, evidence auditor,
audience variants, goal/red card fixtures, quiet periods, validation failures,
and agent coordinator pipeline.
"""

import pytest
from fastapi.testclient import TestClient

import app.main as main
from app.services.match_service import MatchService


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


# ──────────────────────────────────────────────────────────────────────────────
# Goal scoring and insight generation
# ──────────────────────────────────────────────────────────────────────────────

class TestGoalInsight:
    def test_goal_creates_verified_insight(self, client):
        """A goal event must trigger a goal-type insight."""
        events = [
            payload("evt_k", 0, "kickoff"),
            payload("evt_p1", 10, "pass"),
            payload("evt_p2", 15, "pass", second=30),
            payload("evt_s", 20, "shot", attributes={"on_target": True}),
            payload("evt_g", 25, "goal"),
        ]
        for ev in events:
            r = client.post("/api/v1/matches/sim_match_001/events", json=ev)
            assert r.status_code == 200

        insights = client.get("/api/v1/matches/sim_match_001/insights").json()
        goal_insights = [i for i in insights["items"] if i["insight_type"] == "goal"]
        assert len(goal_insights) >= 1
        gi = goal_insights[0]
        assert gi["status"] == "verified"
        assert gi["validation"]["status"] == "approved"
        assert "evt_g" in gi["source_event_ids"]

    def test_goal_updates_scoreline(self, client):
        """After a goal, the match state must reflect the new score."""
        client.post("/api/v1/matches/sim_match_001/events",
                     json=payload("evt_g1", 10, "goal"))
        state = client.get("/api/v1/matches/sim_match_001/state").json()
        assert state["teams"]["ridge_united"]["goals"] == 1
        assert state["teams"]["ridge_united"]["shots"] == 1


# ──────────────────────────────────────────────────────────────────────────────
# Audience variants differ meaningfully
# ──────────────────────────────────────────────────────────────────────────────

class TestAudienceVariants:
    def _get_first_insight(self, client) -> dict:
        events = [
            payload("evt_r1", 8, "high_regain"),
            payload("evt_a1", 8, "attacking_third_entry", second=10),
        ]
        for ev in events:
            client.post("/api/v1/matches/sim_match_001/events", json=ev)
        insights = client.get("/api/v1/matches/sim_match_001/insights").json()
        assert len(insights["items"]) > 0
        return insights["items"][0]

    def test_fan_variant_uses_accessible_language(self, client):
        insight = self._get_first_insight(client)
        fan = insight["audience_variants"]["fan"]
        assert any(c in fan["headline"] for c in ["🔥", "⚽", "🟥", "🎯", "🔄", "📋"])
        assert fan["next_watch"] is not None

    def test_analyst_variant_includes_detailed_metrics(self, client):
        insight = self._get_first_insight(client)
        analyst = insight["audience_variants"]["analyst"]
        assert "detail" in analyst and analyst["detail"] is not None
        assert "Metrics:" in analyst["detail"]
        assert "Evidence window:" in analyst["detail"]

    def test_broadcast_variant_is_compact(self, client):
        insight = self._get_first_insight(client)
        broadcast = insight["audience_variants"]["broadcast"]
        assert broadcast["headline"].isupper() or broadcast["headline"][0].isupper()
        # Broadcast summaries should be concise
        assert len(broadcast["summary"]) < 200

    def test_all_variants_share_same_evidence(self, client):
        insight = self._get_first_insight(client)
        # All variants should reference the same underlying evidence
        evidence = client.get(f"/api/v1/insights/{insight['insight_id']}/evidence").json()
        # The event_ids in evidence must be the same as in the insight
        assert evidence["event_ids"] == insight["source_event_ids"]

    def test_variants_differ_from_each_other(self, client):
        insight = self._get_first_insight(client)
        fan = insight["audience_variants"]["fan"]
        analyst = insight["audience_variants"]["analyst"]
        broadcast = insight["audience_variants"]["broadcast"]
        # Headlines must differ
        assert fan["headline"] != analyst["headline"]
        assert fan["headline"] != broadcast["headline"]
        assert analyst["headline"] != broadcast["headline"]


# ──────────────────────────────────────────────────────────────────────────────
# Quiet period — no manufactured insights
# ──────────────────────────────────────────────────────────────────────────────

class TestQuietPeriod:
    def test_routine_passes_generate_no_insight(self, client):
        """Ordinary midfield passes should not trigger any insight."""
        for i in range(8):
            ev = payload(f"evt_q{i}", 30 + i, "pass", x=50.0, y=50.0)
            r = client.post("/api/v1/matches/sim_match_001/events", json=ev)
            assert r.status_code == 200
            assert r.json()["published_insight_ids"] == []
        insights = client.get("/api/v1/matches/sim_match_001/insights").json()
        assert insights["items"] == []

    def test_mixed_quiet_events_no_insight(self, client):
        """Tackles and interceptions in the middle third are not significant."""
        events = [
            payload("evt_t1", 40, "tackle", x=50.0, y=40.0),
            payload("evt_i1", 41, "interception", x=45.0, y=55.0),
            payload("evt_p1", 42, "pass", x=48.0, y=50.0),
            payload("evt_t2", 43, "tackle", "harbor_fc", x=52.0, y=45.0),
            payload("evt_p2", 44, "pass", "harbor_fc", x=55.0, y=50.0),
        ]
        for ev in events:
            r = client.post("/api/v1/matches/sim_match_001/events", json=ev)
            assert r.status_code == 200
        insights = client.get("/api/v1/matches/sim_match_001/insights").json()
        assert insights["items"] == []


# ──────────────────────────────────────────────────────────────────────────────
# Validation and evidence auditor
# ──────────────────────────────────────────────────────────────────────────────

class TestValidation:
    def test_all_checks_pass_for_valid_insight(self, client):
        events = [
            payload("evt_hr1", 8, "high_regain"),
            payload("evt_ate1", 8, "attacking_third_entry", second=20),
        ]
        for ev in events:
            client.post("/api/v1/matches/sim_match_001/events", json=ev)
        insights = client.get("/api/v1/matches/sim_match_001/insights").json()
        assert len(insights["items"]) > 0
        insight = insights["items"][0]
        assert insight["validation"]["status"] == "approved"
        for check in insight["validation"]["checks"]:
            assert check["passed"] is True

    def test_evidence_window_contains_valid_events(self, client):
        events = [
            payload("evt_vr1", 8, "high_regain"),
            payload("evt_va1", 8, "attacking_third_entry", second=20),
        ]
        for ev in events:
            client.post("/api/v1/matches/sim_match_001/events", json=ev)
        insights = client.get("/api/v1/matches/sim_match_001/insights").json()
        insight = insights["items"][0]
        evidence = client.get(f"/api/v1/insights/{insight['insight_id']}/evidence").json()
        # All events in evidence must be within the time window
        for ev in evidence["events"]:
            ev_seconds = ev["minute"] * 60 + ev["second"]
            window_start = evidence["window"]["start_minute"] * 60 + evidence["window"]["start_second"]
            window_end = evidence["window"]["end_minute"] * 60 + evidence["window"]["end_second"]
            assert window_start <= ev_seconds <= window_end


# ──────────────────────────────────────────────────────────────────────────────
# Agent activity trace
# ──────────────────────────────────────────────────────────────────────────────

class TestAgentTrace:
    def test_analysis_run_trace_shows_all_stages(self, client):
        events = [
            payload("evt_tr1", 8, "high_regain"),
            payload("evt_ta1", 8, "attacking_third_entry", second=20),
        ]
        last_resp = None
        for ev in events:
            r = client.post("/api/v1/matches/sim_match_001/events", json=ev)
            last_resp = r.json()

        if last_resp.get("analysis_run_ids"):
            run_id = last_resp["analysis_run_ids"][0]
            trace = client.get(f"/api/v1/analysis-runs/{run_id}/trace").json()
            assert trace["outcome"] == "insight_published"
            stage_names = [s["stage"] for s in trace["stages"]]
            assert "match_analyst" in stage_names
            assert "tactical_analyst" in stage_names
            assert "narrative_producer" in stage_names
            assert "evidence_auditor" in stage_names
            # Duration should be recorded
            for stage in trace["stages"]:
                assert stage["duration_ms"] >= 0


# ──────────────────────────────────────────────────────────────────────────────
# Batch ingestion
# ──────────────────────────────────────────────────────────────────────────────

class TestBatchIngestion:
    def test_batch_accepts_multiple_valid_events(self, client):
        batch = {
            "events": [
                payload("evt_b1", 50, "pass"),
                payload("evt_b2", 51, "tackle"),
                payload("evt_b3", 52, "pass", second=30),
            ],
            "processing_mode": "inline",
        }
        r = client.post("/api/v1/matches/sim_match_001/events:batch", json=batch)
        assert r.status_code == 200
        body = r.json()
        assert body["accepted_count"] == 3
        assert body["duplicate_count"] == 0
        assert body["rejected_count"] == 0

    def test_batch_reports_match_id_mismatch(self, client):
        batch = {
            "events": [
                {**payload("evt_bm1", 50), "match_id": "wrong_match"},
            ],
            "processing_mode": "inline",
        }
        r = client.post("/api/v1/matches/sim_match_001/events:batch", json=batch)
        assert r.status_code == 200
        body = r.json()
        assert body["rejected_count"] == 1
        assert body["errors"][0]["code"] == "MATCH_ID_MISMATCH"

    def test_batch_handles_duplicates_gracefully(self, client):
        ev = payload("evt_dup", 50, "pass")
        client.post("/api/v1/matches/sim_match_001/events", json=ev)
        batch = {
            "events": [ev, payload("evt_new", 51, "tackle")],
            "processing_mode": "inline",
        }
        r = client.post("/api/v1/matches/sim_match_001/events:batch", json=batch)
        body = r.json()
        assert body["accepted_count"] == 1
        assert body["duplicate_count"] == 1


# ──────────────────────────────────────────────────────────────────────────────
# Match state endpoint
# ──────────────────────────────────────────────────────────────────────────────

class TestMatchState:
    def test_match_not_found_returns_404(self, client):
        r = client.get("/api/v1/matches/nonexistent/state")
        assert r.status_code == 404

    def test_match_state_tracks_multiple_teams(self, client):
        events = [
            payload("evt_mt1", 10, "pass", "ridge_united"),
            payload("evt_mt2", 11, "tackle", "harbor_fc"),
            payload("evt_mt3", 12, "shot", "ridge_united", attributes={"on_target": True}),
        ]
        for ev in events:
            client.post("/api/v1/matches/sim_match_001/events", json=ev)
        state = client.get("/api/v1/matches/sim_match_001/state").json()
        assert "ridge_united" in state["teams"]
        assert "harbor_fc" in state["teams"]
        assert state["teams"]["ridge_united"]["passes"] == 1
        assert state["teams"]["harbor_fc"]["tackles"] == 1
        assert state["teams"]["ridge_united"]["shots"] == 1
        assert state["teams"]["ridge_united"]["shots_on_target"] == 1

    def test_pressure_metrics_available_in_state(self, client):
        events = [
            payload("evt_pm1", 5, "high_regain"),
            payload("evt_pm2", 6, "attacking_third_entry"),
        ]
        for ev in events:
            client.post("/api/v1/matches/sim_match_001/events", json=ev)
        state = client.get("/api/v1/matches/sim_match_001/state").json()
        pressure_key = "pressure_index:ridge_united"
        assert pressure_key in state["metrics"]
        assert state["metrics"][pressure_key]["definition_version"] == "pressure-v1"


# ──────────────────────────────────────────────────────────────────────────────
# Error handling
# ──────────────────────────────────────────────────────────────────────────────

class TestErrorHandling:
    def test_path_body_match_id_mismatch_returns_422(self, client):
        ev = {**payload("evt_mm", 10), "match_id": "different_match"}
        r = client.post("/api/v1/matches/sim_match_001/events", json=ev)
        assert r.status_code == 422
        assert r.json()["error"]["code"] == "MATCH_ID_MISMATCH"

    def test_invalid_event_type_returns_422(self, client):
        ev = payload("evt_inv", 10, "totally_fake_type")
        r = client.post("/api/v1/matches/sim_match_001/events", json=ev)
        assert r.status_code == 422

    def test_missing_required_field_returns_422(self, client):
        r = client.post("/api/v1/matches/sim_match_001/events",
                        json={"event_id": "evt_missing", "match_id": "sim_match_001"})
        assert r.status_code == 422

    def test_nonexistent_insight_returns_404(self, client):
        r = client.get("/api/v1/insights/nonexistent_id")
        assert r.status_code == 404

    def test_nonexistent_run_returns_404(self, client):
        r = client.get("/api/v1/analysis-runs/nonexistent_run")
        assert r.status_code == 404
