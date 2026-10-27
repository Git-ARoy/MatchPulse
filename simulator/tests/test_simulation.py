"""Unit and contract tests for the MatchPulse Synthetic Match Simulator."""

import pytest
from app.domain.events import CanonicalEvent
from simulator.engine.match_sim import MatchSimulation
from simulator.engine.rosters import AVAILABLE_MATCHUPS, build_matchup


def test_matchup_creation():
    assert len(AVAILABLE_MATCHUPS) >= 3
    home, away = build_matchup("epl_mci_ars")
    assert home.name == "Manchester City"
    assert away.name == "Arsenal"
    assert len(home.players) == 11
    assert len(away.players) == 11

    # Check that player positions are within valid pitch bounds
    for p in home.players + away.players:
        assert 0 <= p.base_x <= 100
        assert 0 <= p.base_y <= 100
        assert p.role in ("GK", "CB", "LB", "RB", "CDM", "CM", "CAM", "LW", "RW", "ST")


def test_simulation_clock_and_kickoff():
    emitted = []
    sim = MatchSimulation(match_id="test_sim_01", event_callback=emitted.append)
    assert sim.phase.value == "not_started"

    sim.start()
    assert sim.phase.value == "first_half"
    assert len(emitted) == 1
    assert emitted[0]["event_type"] == "kickoff"

    # Step simulation
    sim.step(10.0)
    assert sim.minute == 0
    assert sim.second == 10

    # Advance 60 seconds
    sim.step(60.0)
    assert sim.minute == 1
    assert sim.second == 10


def test_canonical_event_contract_compliance():
    """Verify that all events emitted by the simulation strictly validate
    against MatchPulse's production Pydantic CanonicalEvent schema.
    """
    emitted = []
    sim = MatchSimulation(match_id="contract_test", event_callback=emitted.append)
    sim.start()

    # Run for 200 simulation steps
    for _ in range(200):
        sim.step(1.0)

    # Inject set pieces to exercise all event types
    sim.inject_free_kick()
    sim.step(3.0)
    sim.inject_penalty()
    sim.step(3.0)
    sim.inject_red_card()
    sim.step(1.0)

    assert len(emitted) >= 5

    # Validate each emitted event against MatchPulse CanonicalEvent
    for event_dict in emitted:
        canonical = CanonicalEvent.model_validate(event_dict)
        assert canonical.match_id == "contract_test"
        assert canonical.schema_version == "event-v1"
        assert 0 <= canonical.minute <= 150
        assert 0 <= canonical.second <= 59
        if canonical.x is not None:
            assert 0 <= canonical.x <= 100
            assert 0 <= canonical.y <= 100


def test_speed_control():
    sim = MatchSimulation(match_id="speed_test")
    sim.start()
    sim.set_speed(10.0)
    sim.step(1.0)
    assert sim.second == 10
