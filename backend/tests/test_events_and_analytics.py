"""Small synthetic fixtures for canonical-event and deterministic-engine tests."""

import pytest
from pydantic import ValidationError

from app.analytics.match_tracker import MatchTracker
from app.analytics.rolling_windows import RollingWindowCalculator
from app.domain.events import CanonicalEvent, EventType, Zone


def event(event_id: str, minute: int, event_type: str = "pass", team_id: str = "ridge_united", **extra):
    attributes = extra.pop("attributes", {"completed": True} if event_type == "pass" else {})
    return CanonicalEvent(
        event_id=event_id,
        match_id="sim_match_001",
        minute=minute,
        second=extra.pop("second", 0),
        event_type=event_type,
        team_id=team_id,
        attributes=attributes,
        **extra,
    )


def test_canonical_event_rejects_bad_identifiers_coordinates_and_attributes():
    with pytest.raises(ValidationError):
        event("bad id", 1)
    with pytest.raises(ValidationError):
        event("evt_1", 1, x=20)
    with pytest.raises(ValidationError):
        event("evt_1", 1, "shot", attributes={"completed": True})
    with pytest.raises(ValidationError):
        event("evt_1", 1, "pressure_event", attributes={"intensity": 101})


def test_tracker_normalizes_zone_and_updates_match_state():
    tracker = MatchTracker("sim_match_001")
    accepted = tracker.process_event(event("evt_pass", 11, x=74, y=20))
    assert accepted.accepted is True
    assert tracker.state.state_version == 1
    assert tracker.state.teams["ridge_united"].passes == 1
    assert tracker.state.teams["ridge_united"].passes_completed == 1
    assert tracker.normalize_event(event("evt_zone", 12, x=74, y=20)).zone == Zone.attacking_third


def test_rolling_windows_have_non_overlapping_boundary_and_pressure_is_clipped():
    rolling = RollingWindowCalculator()
    before = event("evt_before", 0)
    boundary = event("evt_boundary", 5)
    rolling.add_event(before)
    rolling.add_event(boundary)
    assert [item.event_id for item in rolling.get_events_in_window("ridge_united", 10, 0)] == ["evt_boundary"]
    assert [item.event_id for item in rolling.get_previous_window_events("ridge_united", 10, 0)] == ["evt_before"]

    pressure_events = [
        event("evt_attack", 9, "attacking_third_entry"),
        event("evt_regain", 9, "high_regain"),
        event("evt_box", 9, "penalty_box_entry"),
        event("evt_shot", 9, "shot"),
        event("evt_pressure", 9, "pressure_event"),
        event("evt_more", 9, "shot"),
    ]
    score, delta = rolling.calculate_pressure_index("ridge_united", pressure_events, [])
    assert score == 100.0  # 15 + 25 + 20 + 25 + 15 + 25, capped at 100
    assert delta == 100.0
