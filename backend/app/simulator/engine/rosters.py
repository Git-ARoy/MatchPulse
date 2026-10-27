"""Synthetic team rosters and default match configurations.
All player names and rosters are synthetic and fictional in strict compliance
with Premier League competition guidelines.
"""

from __future__ import annotations

from .models import Player, Team


def create_ridge_united(direction: int = 1) -> Team:
    """Ridge United (4-3-3 formation, synthetic fictional club)."""
    def x(val: float) -> float:
        return val if direction == 1 else 100.0 - val

    players = [
        Player("ru_01", "K. Jensen", 1, "ridge_united", "GK", x(5.0), 50.0, speed_rating=78, passing_rating=88, defending_rating=89, shooting_rating=20),
        Player("ru_02", "M. Vance", 2, "ridge_united", "RB", x(22.0), 16.0, speed_rating=90, passing_rating=82, defending_rating=85, shooting_rating=62),
        Player("ru_04", "T. Sterling", 4, "ridge_united", "CB", x(18.0), 38.0, speed_rating=77, passing_rating=80, defending_rating=88, shooting_rating=48),
        Player("ru_05", "D. Mercer", 5, "ridge_united", "CB", x(18.0), 62.0, speed_rating=76, passing_rating=81, defending_rating=89, shooting_rating=45),
        Player("ru_03", "C. Holt", 3, "ridge_united", "LB", x(22.0), 84.0, speed_rating=83, passing_rating=83, defending_rating=84, shooting_rating=60),
        Player("ru_06", "A. Silva", 6, "ridge_united", "CDM", x(32.0), 50.0, speed_rating=78, passing_rating=90, defending_rating=87, shooting_rating=80),
        Player("ru_08", "E. Calder", 8, "ridge_united", "CM", x(42.0), 35.0, speed_rating=80, passing_rating=92, defending_rating=75, shooting_rating=84),
        Player("ru_10", "L. Thorne", 10, "ridge_united", "CM", x(42.0), 65.0, speed_rating=82, passing_rating=89, defending_rating=72, shooting_rating=82),
        Player("ru_07", "N. Hayes", 7, "ridge_united", "RW", x(62.0), 18.0, speed_rating=89, passing_rating=85, defending_rating=58, shooting_rating=86),
        Player("ru_09", "H. Ward", 9, "ridge_united", "ST", x(65.0), 50.0, speed_rating=91, passing_rating=76, defending_rating=48, shooting_rating=94),
        Player("ru_11", "B. Cross", 11, "ridge_united", "LW", x(62.0), 82.0, speed_rating=92, passing_rating=82, defending_rating=52, shooting_rating=81),
    ]
    return Team(
        team_id="ridge_united",
        name="Ridge United",
        short_name="RU",
        primary_color="#38003C",
        secondary_color="#00FF87",
        formation="4-3-3",
        players=players,
        attacking_direction=direction,
    )


def create_harbor_fc(direction: int = -1) -> Team:
    """Harbor FC (4-2-3-1 formation, synthetic fictional club)."""
    def x(val: float) -> float:
        return val if direction == 1 else 100.0 - val

    players = [
        Player("hf_01", "S. Drake", 1, "harbor_fc", "GK", x(5.0), 50.0, speed_rating=76, passing_rating=84, defending_rating=87, shooting_rating=20),
        Player("hf_02", "P. Whitmore", 2, "harbor_fc", "RB", x(22.0), 16.0, speed_rating=82, passing_rating=80, defending_rating=83, shooting_rating=54),
        Player("hf_04", "R. Faulkner", 4, "harbor_fc", "CB", x(18.0), 38.0, speed_rating=81, passing_rating=78, defending_rating=89, shooting_rating=44),
        Player("hf_05", "V. Ramos", 5, "harbor_fc", "CB", x(18.0), 62.0, speed_rating=79, passing_rating=79, defending_rating=88, shooting_rating=56),
        Player("hf_03", "K. Tierney", 3, "harbor_fc", "LB", x(22.0), 84.0, speed_rating=84, passing_rating=81, defending_rating=81, shooting_rating=52),
        Player("hf_06", "J. Bennett", 6, "harbor_fc", "CDM", x(32.0), 40.0, speed_rating=77, passing_rating=85, defending_rating=86, shooting_rating=72),
        Player("hf_08", "M. Kovac", 8, "harbor_fc", "CDM", x(32.0), 60.0, speed_rating=74, passing_rating=86, defending_rating=82, shooting_rating=75),
        Player("hf_07", "D. Sako", 7, "harbor_fc", "RW", x(60.0), 18.0, speed_rating=88, passing_rating=84, defending_rating=60, shooting_rating=84),
        Player("hf_10", "F. Sorenson", 10, "harbor_fc", "CAM", x(48.0), 50.0, speed_rating=80, passing_rating=90, defending_rating=65, shooting_rating=85),
        Player("hf_11", "G. Marin", 11, "harbor_fc", "LW", x(60.0), 82.0, speed_rating=89, passing_rating=81, defending_rating=55, shooting_rating=80),
        Player("hf_09", "C. Aris", 9, "harbor_fc", "ST", x(64.0), 50.0, speed_rating=83, passing_rating=79, defending_rating=52, shooting_rating=85),
    ]
    return Team(
        team_id="harbor_fc",
        name="Harbor FC",
        short_name="HF",
        primary_color="#00FF87",
        secondary_color="#38003C",
        formation="4-2-3-1",
        players=players,
        attacking_direction=direction,
    )


def create_city_synthetic(direction: int = 1) -> Team:
    """Manchester City (4-3-3 formation, synthetic fictional player roster)."""
    def x(val: float) -> float:
        return val if direction == 1 else 100.0 - val

    players = [
        Player("cty_31", "E. Morales", 31, "manchester_city", "GK", x(5.0), 50.0, speed_rating=78, passing_rating=91, defending_rating=89, shooting_rating=20),
        Player("cty_02", "K. Walker-Smith", 2, "manchester_city", "RB", x(22.0), 16.0, speed_rating=91, passing_rating=78, defending_rating=84, shooting_rating=58),
        Player("cty_05", "J. Stonefield", 5, "manchester_city", "CB", x(18.0), 38.0, speed_rating=76, passing_rating=85, defending_rating=87, shooting_rating=55),
        Player("cty_03", "R. Davies", 3, "manchester_city", "CB", x(18.0), 62.0, speed_rating=75, passing_rating=80, defending_rating=89, shooting_rating=45),
        Player("cty_24", "J. Vardis", 24, "manchester_city", "LB", x(22.0), 84.0, speed_rating=82, passing_rating=84, defending_rating=86, shooting_rating=65),
        Player("cty_16", "R. Rodrigo", 16, "manchester_city", "CDM", x(32.0), 50.0, speed_rating=74, passing_rating=91, defending_rating=89, shooting_rating=82),
        Player("cty_17", "K. Brand", 17, "manchester_city", "CM", x(42.0), 35.0, speed_rating=76, passing_rating=95, defending_rating=70, shooting_rating=88),
        Player("cty_20", "B. Silva-Santos", 20, "manchester_city", "CM", x(42.0), 65.0, speed_rating=80, passing_rating=89, defending_rating=75, shooting_rating=78),
        Player("cty_47", "P. Ford", 47, "manchester_city", "RW", x(62.0), 18.0, speed_rating=86, passing_rating=88, defending_rating=62, shooting_rating=86),
        Player("cty_09", "E. Holand", 9, "manchester_city", "ST", x(65.0), 50.0, speed_rating=90, passing_rating=72, defending_rating=45, shooting_rating=96),
        Player("cty_11", "J. Doko", 11, "manchester_city", "LW", x(62.0), 82.0, speed_rating=93, passing_rating=80, defending_rating=48, shooting_rating=77),
    ]
    return Team(
        team_id="manchester_city",
        name="Manchester City",
        short_name="MCI",
        primary_color="#6CABDD",
        secondary_color="#1C2C5B",
        formation="4-3-3",
        players=players,
        attacking_direction=direction,
    )


def create_north_london_synthetic(direction: int = -1) -> Team:
    """Arsenal (4-2-3-1 formation, synthetic fictional player roster)."""
    def x(val: float) -> float:
        return val if direction == 1 else 100.0 - val

    players = [
        Player("nld_22", "D. Ray", 22, "arsenal", "GK", x(5.0), 50.0, speed_rating=75, passing_rating=86, defending_rating=88, shooting_rating=20),
        Player("nld_04", "B. Whyte", 4, "arsenal", "RB", x(22.0), 16.0, speed_rating=79, passing_rating=81, defending_rating=83, shooting_rating=52),
        Player("nld_02", "W. Sabo", 2, "arsenal", "CB", x(18.0), 38.0, speed_rating=84, passing_rating=82, defending_rating=89, shooting_rating=42),
        Player("nld_06", "G. Magno", 6, "arsenal", "CB", x(18.0), 62.0, speed_rating=78, passing_rating=77, defending_rating=88, shooting_rating=62),
        Player("nld_12", "J. Timber-Jones", 12, "arsenal", "LB", x(22.0), 84.0, speed_rating=82, passing_rating=81, defending_rating=82, shooting_rating=50),
        Player("nld_41", "D. Royce", 41, "arsenal", "CDM", x(32.0), 40.0, speed_rating=78, passing_rating=84, defending_rating=88, shooting_rating=75),
        Player("nld_05", "T. Parker", 5, "arsenal", "CDM", x(32.0), 60.0, speed_rating=72, passing_rating=83, defending_rating=83, shooting_rating=74),
        Player("nld_07", "B. Saki", 7, "arsenal", "RW", x(60.0), 18.0, speed_rating=88, passing_rating=86, defending_rating=65, shooting_rating=85),
        Player("nld_08", "M. Oden", 8, "arsenal", "CAM", x(48.0), 50.0, speed_rating=78, passing_rating=91, defending_rating=68, shooting_rating=84),
        Player("nld_11", "G. Marten", 11, "arsenal", "LW", x(60.0), 82.0, speed_rating=91, passing_rating=79, defending_rating=58, shooting_rating=79),
        Player("nld_29", "K. Havel", 29, "arsenal", "ST", x(64.0), 50.0, speed_rating=80, passing_rating=82, defending_rating=60, shooting_rating=82),
    ]
    return Team(
        team_id="arsenal",
        name="Arsenal",
        short_name="ARS",
        primary_color="#EF0107",
        secondary_color="#063672",
        formation="4-2-3-1",
        players=players,
        attacking_direction=direction,
    )


def create_coast_albion(direction: int = 1) -> Team:
    """Liverpool (4-3-3 formation, synthetic fictional player roster)."""
    def x(val: float) -> float:
        return val if direction == 1 else 100.0 - val

    players = [
        Player("cst_01", "A. Becker-Cole", 1, "liverpool", "GK", x(5.0), 50.0, speed_rating=78, passing_rating=87, defending_rating=90, shooting_rating=20),
        Player("cst_66", "T. Arnold-Evans", 66, "liverpool", "RB", x(22.0), 16.0, speed_rating=79, passing_rating=92, defending_rating=78, shooting_rating=75),
        Player("cst_04", "V. Dijkman", 4, "liverpool", "CB", x(18.0), 38.0, speed_rating=81, passing_rating=84, defending_rating=91, shooting_rating=58),
        Player("cst_05", "I. Konan", 5, "liverpool", "CB", x(18.0), 62.0, speed_rating=82, passing_rating=76, defending_rating=87, shooting_rating=42),
        Player("cst_26", "A. Robertson-Hill", 26, "liverpool", "LB", x(22.0), 84.0, speed_rating=83, passing_rating=84, defending_rating=83, shooting_rating=60),
        Player("cst_10", "A. MacIntyre", 10, "liverpool", "CDM", x(32.0), 50.0, speed_rating=75, passing_rating=88, defending_rating=82, shooting_rating=80),
        Player("cst_08", "D. Sobor", 8, "liverpool", "CM", x(42.0), 35.0, speed_rating=84, passing_rating=87, defending_rating=75, shooting_rating=86),
        Player("cst_17", "C. Jonestone", 17, "liverpool", "CM", x(42.0), 65.0, speed_rating=79, passing_rating=83, defending_rating=77, shooting_rating=76),
        Player("cst_11", "M. Solari", 11, "liverpool", "RW", x(64.0), 18.0, speed_rating=90, passing_rating=88, defending_rating=50, shooting_rating=92),
        Player("cst_09", "D. Nuno", 9, "liverpool", "ST", x(66.0), 50.0, speed_rating=92, passing_rating=74, defending_rating=52, shooting_rating=85),
        Player("cst_07", "L. Diaz-Rey", 7, "liverpool", "LW", x(64.0), 82.0, speed_rating=91, passing_rating=81, defending_rating=56, shooting_rating=82),
    ]
    return Team(
        team_id="liverpool",
        name="Liverpool",
        short_name="LIV",
        primary_color="#C8102E",
        secondary_color="#00B2A9",
        formation="4-3-3",
        players=players,
        attacking_direction=direction,
    )


def create_vale_athletic(direction: int = -1) -> Team:
    """Chelsea (4-2-3-1 formation, synthetic fictional player roster)."""
    def x(val: float) -> float:
        return val if direction == 1 else 100.0 - val

    players = [
        Player("vle_01", "R. Sanchez-Perez", 1, "chelsea", "GK", x(5.0), 50.0, speed_rating=73, passing_rating=79, defending_rating=83, shooting_rating=20),
        Player("vle_27", "M. Gusti", 27, "chelsea", "RB", x(22.0), 16.0, speed_rating=87, passing_rating=78, defending_rating=79, shooting_rating=56),
        Player("vle_29", "W. Fontana", 29, "chelsea", "CB", x(18.0), 38.0, speed_rating=82, passing_rating=76, defending_rating=83, shooting_rating=42),
        Player("vle_06", "L. Colwyn", 6, "chelsea", "CB", x(18.0), 62.0, speed_rating=79, passing_rating=82, defending_rating=84, shooting_rating=46),
        Player("vle_03", "M. Cuckoo", 3, "chelsea", "LB", x(22.0), 84.0, speed_rating=82, passing_rating=80, defending_rating=83, shooting_rating=59),
        Player("vle_25", "M. Cardenas", 25, "chelsea", "CDM", x(32.0), 40.0, speed_rating=81, passing_rating=83, defending_rating=87, shooting_rating=69),
        Player("vle_08", "E. Fernandez-Cruz", 8, "chelsea", "CDM", x(32.0), 60.0, speed_rating=74, passing_rating=89, defending_rating=79, shooting_rating=77),
        Player("vle_11", "N. Madero", 11, "chelsea", "RW", x(60.0), 18.0, speed_rating=89, passing_rating=79, defending_rating=46, shooting_rating=79),
        Player("vle_20", "C. Palmer-Hale", 20, "chelsea", "CAM", x(48.0), 50.0, speed_rating=82, passing_rating=90, defending_rating=62, shooting_rating=88),
        Player("vle_19", "J. Sanders", 19, "chelsea", "LW", x(60.0), 82.0, speed_rating=85, passing_rating=84, defending_rating=50, shooting_rating=78),
        Player("vle_15", "N. Jax", 15, "chelsea", "ST", x(64.0), 50.0, speed_rating=87, passing_rating=76, defending_rating=50, shooting_rating=82),
    ]
    return Team(
        team_id="chelsea",
        name="Chelsea",
        short_name="CHE",
        primary_color="#034694",
        secondary_color="#EE242C",
        formation="4-2-3-1",
        players=players,
        attacking_direction=direction,
    )


AVAILABLE_MATCHUPS = [
    {
        "id": "epl_mci_ars",
        "title": "Manchester City vs. Arsenal",
        "home": "manchester_city",
        "away": "arsenal",
        "home_factory": create_city_synthetic,
        "away_factory": create_north_london_synthetic,
    },
    {
        "id": "synthetic_ridge_harbor",
        "title": "Ridge United vs. Harbor FC",
        "home": "ridge_united",
        "away": "harbor_fc",
        "home_factory": create_ridge_united,
        "away_factory": create_harbor_fc,
    },
    {
        "id": "epl_liv_che",
        "title": "Liverpool vs. Chelsea",
        "home": "liverpool",
        "away": "chelsea",
        "home_factory": create_coast_albion,
        "away_factory": create_vale_athletic,
    },
]


def build_matchup(matchup_id: str) -> tuple[Team, Team]:
    """Retrieve home and away team instances for the chosen matchup."""
    for item in AVAILABLE_MATCHUPS:
        if item["id"] == matchup_id:
            return item["home_factory"](direction=1), item["away_factory"](direction=-1)
    # Default to Ridge United vs Harbor FC
    return create_ridge_united(direction=1), create_harbor_fc(direction=-1)
