import json

from app.adapters.statsbomb_open_data import StatsBombOpenDataAdapter
from app.domain.events import EventType, Zone


def test_statsbomb_open_data_is_normalized_without_losing_provenance(tmp_path):
    root = tmp_path
    (root / "data" / "events").mkdir(parents=True)
    (root / "data" / "matches").mkdir(parents=True)
    (root / "data" / "matches" / "2").mkdir()
    (root / "data" / "matches" / "2" / "27.json").write_text(json.dumps([{
        "match_id": 123,
        "match_date": "2020-01-01",
        "home_team": {"home_team_name": "Ridge United"},
        "away_team": {"away_team_name": "Harbor FC"},
        "competition": {"competition_name": "Open Data Cup"},
        "season": {"season_name": "2020"},
    }]))
    (root / "data" / "events" / "123.json").write_text(json.dumps([
        {"id": "shot-1", "minute": 4, "second": 2, "type": {"name": "Shot"}, "team": {"id": 10}, "player": {"id": 8}, "location": [96, 40], "shot": {"outcome": {"name": "Goal"}}},
        {"id": "pass-1", "minute": 3, "second": 1, "type": {"name": "Pass"}, "team": {"id": 10}, "player": {"id": 7}, "location": [70, 40], "pass": {"recipient": {"id": 8}}},
    ]))

    adapter = StatsBombOpenDataAdapter(root)
    summary, events = adapter.load_match("123")

    assert summary is not None
    assert summary.match_id == "statsbomb_123"
    assert [event.event_id for event in events] == ["pass-1", "shot-1"]
    assert events[0].event_type == EventType.pass_
    assert events[0].source.adapter == "statsbomb-open-data"
    assert events[1].event_type == EventType.goal
    assert events[1].zone == Zone.attacking_third
