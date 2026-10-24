"""Small, labelled synthetic fixtures for exercising the live vertical slice.

These are deliberately short event sequences rather than a match simulator.
They use fictional teams and the canonical event contract, so they are safe
for the hackathon's synthetic-data requirement and replaceable in deployment.
"""

from __future__ import annotations

from app.domain.events import CanonicalEvent, EventType, Zone

FIXTURE_NAMES = ("pressure-swing", "goal-sequence", "quiet-period")


def _event(
    fixture: str, number: int, match_id: str, minute: int, second: int,
    event_type: EventType, team_id: str, player_id: str, *, zone: Zone | None = None,
    attributes: dict | None = None,
) -> CanonicalEvent:
    return CanonicalEvent(
        event_id=f"fixture_{fixture.replace('-', '_')}_{number}",
        match_id=match_id,
        minute=minute,
        second=second,
        event_type=event_type,
        team_id=team_id,
        player_id=player_id,
        zone=zone,
        attributes=attributes or {},
        source={"adapter": "synthetic-dev-fixture", "source_event_id": f"{fixture}-{number}"},
    )


def build_fixture(name: str, match_id: str) -> list[CanonicalEvent]:
    """Build one chronological, intentionally small canonical event sequence."""
    if name == "pressure-swing":
        return [
            _event(name, 1, match_id, 1, 0, EventType.pass_, "ridge_united", "ridge_08", zone=Zone.middle_third, attributes={"completed": True}),
            _event(name, 2, match_id, 8, 0, EventType.high_regain, "ridge_united", "ridge_06", zone=Zone.attacking_third),
            _event(name, 3, match_id, 8, 10, EventType.attacking_third_entry, "ridge_united", "ridge_10", zone=Zone.attacking_third),
        ]
    if name == "goal-sequence":
        return [
            _event(name, 1, match_id, 0, 0, EventType.kickoff, "ridge_united", "ridge_09", zone=Zone.middle_third),
            _event(name, 2, match_id, 12, 0, EventType.pass_, "ridge_united", "ridge_08", zone=Zone.attacking_third, attributes={"completed": True, "recipient_player_id": "ridge_09"}),
            _event(name, 3, match_id, 12, 20, EventType.shot, "ridge_united", "ridge_09", zone=Zone.penalty_box, attributes={"on_target": True, "outcome": "goal"}),
            _event(name, 4, match_id, 12, 22, EventType.goal, "ridge_united", "ridge_09", zone=Zone.penalty_box, attributes={"outcome": "goal"}),
        ]
    if name == "quiet-period":
        return [
            _event(name, 1, match_id, 30, 0, EventType.pass_, "harbor_fc", "harbor_04", zone=Zone.middle_third, attributes={"completed": True}),
            _event(name, 2, match_id, 31, 0, EventType.tackle, "ridge_united", "ridge_06", zone=Zone.middle_third),
            _event(name, 3, match_id, 32, 0, EventType.pass_, "harbor_fc", "harbor_08", zone=Zone.middle_third, attributes={"completed": True}),
            _event(name, 4, match_id, 33, 0, EventType.interception, "ridge_united", "ridge_05", zone=Zone.middle_third),
        ]
    raise ValueError(f"unknown fixture '{name}'")
