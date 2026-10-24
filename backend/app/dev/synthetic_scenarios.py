"""Safe, football-realistic synthetic showcase scenarios for the public demo.

These events are authored for MatchPulse. Teams, players, scores and values
are fictional and never represent a real Premier League match or feed.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.events import CanonicalEvent, EventType, Zone


@dataclass(frozen=True)
class SyntheticScenario:
    scenario_id: str
    title: str
    description: str
    match_id: str
    home_team_id: str
    away_team_id: str
    home_team_name: str
    away_team_name: str


SHOWCASE_MATCH_ID = "synthetic_ridge_harbor"
SHOWCASE_SCENARIOS = {
    "momentum-surge": SyntheticScenario(
        scenario_id="momentum-surge",
        title="Momentum surge",
        description="A fictional five-minute pressure swing followed by a scored goal.",
        match_id=SHOWCASE_MATCH_ID,
        home_team_id="ridge_united",
        away_team_id="harbor_fc",
        home_team_name="Ridge United",
        away_team_name="Harbor FC",
    ),
    "quiet-period": SyntheticScenario(
        scenario_id="quiet-period",
        title="Quiet period",
        description="A routine fictional midfield sequence that should not create a narrative.",
        match_id="synthetic_quiet_period",
        home_team_id="ridge_united",
        away_team_id="harbor_fc",
        home_team_name="Ridge United",
        away_team_name="Harbor FC",
    ),
}


def _event(
    scenario: str, number: int, match_id: str, minute: int, second: int,
    event_type: EventType, team_id: str, player_id: str, x: float, y: float,
    zone: Zone, attributes: dict | None = None,
) -> CanonicalEvent:
    return CanonicalEvent(
        event_id=f"synthetic_{scenario.replace('-', '_')}_{number}",
        match_id=match_id,
        minute=minute,
        second=second,
        event_type=event_type,
        team_id=team_id,
        player_id=player_id,
        x=x,
        y=y,
        zone=zone,
        attributes=attributes or {},
        source={"adapter": "synthetic-showcase", "source_event_id": f"{scenario}-{number}", "raw_metadata": {"synthetic": True}},
    )


def list_scenarios() -> list[SyntheticScenario]:
    return list(SHOWCASE_SCENARIOS.values())


def build_scenario(scenario_id: str) -> list[CanonicalEvent]:
    scenario = SHOWCASE_SCENARIOS[scenario_id]
    if scenario_id == "quiet-period":
        return [
            _event(scenario_id, 1, scenario.match_id, 30, 0, EventType.kickoff, "ridge_united", "ridge_09", 50, 50, Zone.middle_third),
            _event(scenario_id, 2, scenario.match_id, 30, 22, EventType.pass_, "harbor_fc", "harbor_04", 46, 52, Zone.middle_third, {"completed": True, "distance_m": 8.2, "difficulty_rating": 12}),
            _event(scenario_id, 3, scenario.match_id, 31, 5, EventType.tackle, "ridge_united", "ridge_06", 50, 48, Zone.middle_third),
            _event(scenario_id, 4, scenario.match_id, 31, 42, EventType.pass_, "harbor_fc", "harbor_08", 52, 46, Zone.middle_third, {"completed": True, "distance_m": 11.4, "difficulty_rating": 18}),
            _event(scenario_id, 5, scenario.match_id, 32, 10, EventType.interception, "ridge_united", "ridge_05", 48, 55, Zone.middle_third),
        ]
    return [
        _event(scenario_id, 1, scenario.match_id, 0, 0, EventType.kickoff, "ridge_united", "ridge_09", 50, 50, Zone.middle_third),
        _event(scenario_id, 2, scenario.match_id, 1, 10, EventType.pass_, "harbor_fc", "harbor_04", 44, 51, Zone.middle_third, {"completed": True, "distance_m": 9.4, "difficulty_rating": 14}),
        _event(scenario_id, 3, scenario.match_id, 2, 15, EventType.pass_, "ridge_united", "ridge_08", 55, 44, Zone.middle_third, {"completed": True, "distance_m": 13.7, "difficulty_rating": 28}),
        _event(scenario_id, 4, scenario.match_id, 5, 12, EventType.high_regain, "ridge_united", "ridge_06", 76, 42, Zone.attacking_third),
        _event(scenario_id, 5, scenario.match_id, 5, 25, EventType.pressure_event, "ridge_united", "ridge_10", 80, 38, Zone.attacking_third, {"intensity": 82}),
        _event(scenario_id, 6, scenario.match_id, 5, 34, EventType.attacking_third_entry, "ridge_united", "ridge_11", 76, 30, Zone.attacking_third),
        _event(scenario_id, 7, scenario.match_id, 5, 42, EventType.penalty_box_entry, "ridge_united", "ridge_09", 88, 48, Zone.penalty_box),
        _event(scenario_id, 8, scenario.match_id, 5, 49, EventType.pass_, "ridge_united", "ridge_10", 82, 38, Zone.attacking_third, {"completed": True, "recipient_player_id": "ridge_09", "distance_m": 14.8, "difficulty_rating": 68}),
        _event(scenario_id, 9, scenario.match_id, 5, 55, EventType.shot, "ridge_united", "ridge_09", 91, 49, Zone.penalty_box, {"on_target": True, "outcome": "goal", "speed_kph": 103.4}),
        _event(scenario_id, 10, scenario.match_id, 5, 57, EventType.goal, "ridge_united", "ridge_09", 96, 50, Zone.penalty_box, {"outcome": "goal", "on_target": True, "speed_kph": 103.4}),
    ]
