"""Premier League team rosters and default match configurations."""

from __future__ import annotations

from simulator.engine.models import Player, Team


def create_manchester_city(direction: int = 1) -> Team:
    """Manchester City (4-3-3 formation)."""
    # If direction is 1 (left to right, home): GK is near x=5, FW near x=75.
    # If direction is -1 (right to left, away): GK is near x=95, FW near x=25.
    def x(val: float) -> float:
        return val if direction == 1 else 100.0 - val

    players = [
        Player("mci_31", "Ederson", 31, "manchester_city", "GK", x(5.0), 50.0, speed_rating=78, passing_rating=91, defending_rating=89, shooting_rating=20),
        Player("mci_02", "Kyle Walker", 2, "manchester_city", "RB", x(22.0), 16.0, speed_rating=91, passing_rating=78, defending_rating=84, shooting_rating=58),
        Player("mci_05", "John Stones", 5, "manchester_city", "CB", x(18.0), 38.0, speed_rating=76, passing_rating=85, defending_rating=87, shooting_rating=55),
        Player("mci_03", "Ruben Dias", 3, "manchester_city", "CB", x(18.0), 62.0, speed_rating=75, passing_rating=80, defending_rating=89, shooting_rating=45),
        Player("mci_24", "Josko Gvardiol", 24, "manchester_city", "LB", x(22.0), 84.0, speed_rating=82, passing_rating=84, defending_rating=86, shooting_rating=65),
        Player("mci_16", "Rodri", 16, "manchester_city", "CDM", x(32.0), 50.0, speed_rating=74, passing_rating=91, defending_rating=89, shooting_rating=82),
        Player("mci_17", "Kevin De Bruyne", 17, "manchester_city", "CM", x(42.0), 35.0, speed_rating=76, passing_rating=95, defending_rating=70, shooting_rating=88),
        Player("mci_20", "Bernardo Silva", 20, "manchester_city", "CM", x(42.0), 65.0, speed_rating=80, passing_rating=89, defending_rating=75, shooting_rating=78),
        Player("mci_47", "Phil Foden", 47, "manchester_city", "RW", x(62.0), 18.0, speed_rating=86, passing_rating=88, defending_rating=62, shooting_rating=86),
        Player("mci_09", "Erling Haaland", 9, "manchester_city", "ST", x(65.0), 50.0, speed_rating=90, passing_rating=72, defending_rating=45, shooting_rating=96),
        Player("mci_11", "Jeremy Doku", 11, "manchester_city", "LW", x(62.0), 82.0, speed_rating=93, passing_rating=80, defending_rating=48, shooting_rating=77),
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


def create_arsenal(direction: int = -1) -> Team:
    """Arsenal (4-2-3-1 formation)."""
    def x(val: float) -> float:
        return val if direction == 1 else 100.0 - val

    players = [
        Player("ars_22", "David Raya", 22, "arsenal", "GK", x(5.0), 50.0, speed_rating=75, passing_rating=86, defending_rating=88, shooting_rating=20),
        Player("ars_04", "Ben White", 4, "arsenal", "RB", x(22.0), 16.0, speed_rating=79, passing_rating=81, defending_rating=83, shooting_rating=52),
        Player("ars_02", "William Saliba", 2, "arsenal", "CB", x(18.0), 38.0, speed_rating=84, passing_rating=82, defending_rating=89, shooting_rating=42),
        Player("ars_06", "Gabriel Magalhaes", 6, "arsenal", "CB", x(18.0), 62.0, speed_rating=78, passing_rating=77, defending_rating=88, shooting_rating=62),
        Player("ars_12", "Jurrien Timber", 12, "arsenal", "LB", x(22.0), 84.0, speed_rating=82, passing_rating=81, defending_rating=82, shooting_rating=50),
        Player("ars_41", "Declan Rice", 41, "arsenal", "CDM", x(32.0), 40.0, speed_rating=78, passing_rating=84, defending_rating=88, shooting_rating=75),
        Player("ars_05", "Thomas Partey", 5, "arsenal", "CDM", x(32.0), 60.0, speed_rating=72, passing_rating=83, defending_rating=83, shooting_rating=74),
        Player("ars_07", "Bukayo Saka", 7, "arsenal", "RW", x(60.0), 18.0, speed_rating=88, passing_rating=86, defending_rating=65, shooting_rating=85),
        Player("ars_08", "Martin Odegaard", 8, "arsenal", "CAM", x(48.0), 50.0, speed_rating=78, passing_rating=91, defending_rating=68, shooting_rating=84),
        Player("ars_11", "Gabriel Martinelli", 11, "arsenal", "LW", x(60.0), 82.0, speed_rating=91, passing_rating=79, defending_rating=58, shooting_rating=79),
        Player("ars_29", "Kai Havertz", 29, "arsenal", "ST", x(64.0), 50.0, speed_rating=80, passing_rating=82, defending_rating=60, shooting_rating=82),
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


def create_liverpool(direction: int = 1) -> Team:
    """Liverpool (4-3-3 formation)."""
    def x(val: float) -> float:
        return val if direction == 1 else 100.0 - val

    players = [
        Player("liv_01", "Alisson Becker", 1, "liverpool", "GK", x(5.0), 50.0, speed_rating=78, passing_rating=87, defending_rating=91, shooting_rating=20),
        Player("liv_66", "Trent Alexander-Arnold", 66, "liverpool", "RB", x(22.0), 16.0, speed_rating=77, passing_rating=93, defending_rating=76, shooting_rating=78),
        Player("liv_05", "Ibrahima Konate", 5, "liverpool", "CB", x(18.0), 38.0, speed_rating=83, passing_rating=74, defending_rating=86, shooting_rating=40),
        Player("liv_04", "Virgil van Dijk", 4, "liverpool", "CB", x(18.0), 62.0, speed_rating=80, passing_rating=83, defending_rating=91, shooting_rating=60),
        Player("liv_26", "Andy Robertson", 26, "liverpool", "LB", x(22.0), 84.0, speed_rating=82, passing_rating=83, defending_rating=82, shooting_rating=62),
        Player("liv_10", "Alexis Mac Allister", 10, "liverpool", "CDM", x(32.0), 50.0, speed_rating=74, passing_rating=87, defending_rating=80, shooting_rating=81),
        Player("liv_08", "Dominik Szoboszlai", 8, "liverpool", "CM", x(42.0), 35.0, speed_rating=83, passing_rating=86, defending_rating=74, shooting_rating=85),
        Player("liv_17", "Curtis Jones", 17, "liverpool", "CM", x(42.0), 65.0, speed_rating=78, passing_rating=82, defending_rating=76, shooting_rating=75),
        Player("liv_11", "Mohamed Salah", 11, "liverpool", "RW", x(64.0), 18.0, speed_rating=89, passing_rating=87, defending_rating=48, shooting_rating=91),
        Player("liv_09", "Darwin Nunez", 9, "liverpool", "ST", x(66.0), 50.0, speed_rating=91, passing_rating=73, defending_rating=50, shooting_rating=84),
        Player("liv_07", "Luis Diaz", 7, "liverpool", "LW", x(64.0), 82.0, speed_rating=90, passing_rating=80, defending_rating=55, shooting_rating=81),
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


def create_chelsea(direction: int = -1) -> Team:
    """Chelsea (4-2-3-1 formation)."""
    def x(val: float) -> float:
        return val if direction == 1 else 100.0 - val

    players = [
        Player("che_01", "Robert Sanchez", 1, "chelsea", "GK", x(5.0), 50.0, speed_rating=72, passing_rating=78, defending_rating=82, shooting_rating=20),
        Player("che_27", "Malo Gusto", 27, "chelsea", "RB", x(22.0), 16.0, speed_rating=86, passing_rating=77, defending_rating=78, shooting_rating=55),
        Player("che_29", "Wesley Fofana", 29, "chelsea", "CB", x(18.0), 38.0, speed_rating=81, passing_rating=75, defending_rating=82, shooting_rating=40),
        Player("che_06", "Levi Colwill", 6, "chelsea", "CB", x(18.0), 62.0, speed_rating=78, passing_rating=81, defending_rating=83, shooting_rating=45),
        Player("che_03", "Marc Cucurella", 3, "chelsea", "LB", x(22.0), 84.0, speed_rating=81, passing_rating=79, defending_rating=82, shooting_rating=58),
        Player("che_25", "Moises Caicedo", 25, "chelsea", "CDM", x(32.0), 40.0, speed_rating=80, passing_rating=82, defending_rating=86, shooting_rating=68),
        Player("che_08", "Enzo Fernandez", 8, "chelsea", "CDM", x(32.0), 60.0, speed_rating=73, passing_rating=88, defending_rating=78, shooting_rating=76),
        Player("che_11", "Noni Madueke", 11, "chelsea", "RW", x(60.0), 18.0, speed_rating=88, passing_rating=78, defending_rating=45, shooting_rating=78),
        Player("che_20", "Cole Palmer", 20, "chelsea", "CAM", x(48.0), 50.0, speed_rating=81, passing_rating=89, defending_rating=60, shooting_rating=87),
        Player("che_19", "Jadon Sancho", 19, "chelsea", "LW", x(60.0), 82.0, speed_rating=84, passing_rating=83, defending_rating=48, shooting_rating=77),
        Player("che_15", "Nicolas Jackson", 15, "chelsea", "ST", x(64.0), 50.0, speed_rating=86, passing_rating=75, defending_rating=48, shooting_rating=81),
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


def create_tottenham(direction: int = 1) -> Team:
    """Tottenham Hotspur (4-3-3 formation)."""
    def x(val: float) -> float:
        return val if direction == 1 else 100.0 - val

    players = [
        Player("tot_01", "Guglielmo Vicario", 1, "tottenham", "GK", x(5.0), 50.0, speed_rating=76, passing_rating=79, defending_rating=85, shooting_rating=20),
        Player("tot_23", "Pedro Porro", 23, "tottenham", "RB", x(22.0), 16.0, speed_rating=84, passing_rating=82, defending_rating=78, shooting_rating=74),
        Player("tot_17", "Cristian Romero", 17, "tottenham", "CB", x(18.0), 38.0, speed_rating=81, passing_rating=79, defending_rating=87, aggression_rating=88, shooting_rating=52),
        Player("tot_37", "Micky van de Ven", 37, "tottenham", "CB", x(18.0), 62.0, speed_rating=94, passing_rating=76, defending_rating=84, shooting_rating=45),
        Player("tot_13", "Destiny Udogie", 13, "tottenham", "LB", x(22.0), 84.0, speed_rating=86, passing_rating=78, defending_rating=80, shooting_rating=62),
        Player("tot_08", "Yves Bissouma", 8, "tottenham", "CDM", x(32.0), 50.0, speed_rating=79, passing_rating=81, defending_rating=82, shooting_rating=68),
        Player("tot_10", "James Maddison", 10, "tottenham", "CM", x(42.0), 35.0, speed_rating=76, passing_rating=88, defending_rating=62, shooting_rating=84),
        Player("tot_29", "Pape Matar Sarr", 29, "tottenham", "CM", x(42.0), 65.0, speed_rating=82, passing_rating=79, defending_rating=78, shooting_rating=72),
        Player("tot_22", "Brennan Johnson", 22, "tottenham", "RW", x(62.0), 18.0, speed_rating=91, passing_rating=76, defending_rating=52, shooting_rating=79),
        Player("tot_19", "Dominic Solanke", 19, "tottenham", "ST", x(64.0), 50.0, speed_rating=83, passing_rating=74, defending_rating=55, shooting_rating=82),
        Player("tot_07", "Son Heung-min", 7, "tottenham", "LW", x(62.0), 82.0, speed_rating=87, passing_rating=84, defending_rating=50, shooting_rating=88),
    ]
    return Team(
        team_id="tottenham",
        name="Tottenham Hotspur",
        short_name="TOT",
        primary_color="#132257",
        secondary_color="#FFFFFF",
        formation="4-3-3",
        players=players,
        attacking_direction=direction,
    )


def create_manchester_united(direction: int = -1) -> Team:
    """Manchester United (4-2-3-1 formation)."""
    def x(val: float) -> float:
        return val if direction == 1 else 100.0 - val

    players = [
        Player("mun_24", "Andre Onana", 24, "manchester_united", "GK", x(5.0), 50.0, speed_rating=74, passing_rating=85, defending_rating=83, shooting_rating=20),
        Player("mun_03", "Noussair Mazraoui", 3, "manchester_united", "RB", x(22.0), 16.0, speed_rating=80, passing_rating=79, defending_rating=79, shooting_rating=60),
        Player("mun_04", "Matthijs de Ligt", 4, "manchester_united", "CB", x(18.0), 38.0, speed_rating=77, passing_rating=78, defending_rating=85, shooting_rating=55),
        Player("mun_06", "Lisandro Martinez", 6, "manchester_united", "CB", x(18.0), 62.0, speed_rating=79, passing_rating=82, defending_rating=86, aggression_rating=85, shooting_rating=50),
        Player("mun_20", "Diogo Dalot", 20, "manchester_united", "LB", x(22.0), 84.0, speed_rating=82, passing_rating=79, defending_rating=80, shooting_rating=64),
        Player("mun_37", "Kobbie Mainoo", 37, "manchester_united", "CDM", x(32.0), 40.0, speed_rating=76, passing_rating=84, defending_rating=80, shooting_rating=74),
        Player("mun_18", "Casemiro", 18, "manchester_united", "CDM", x(32.0), 60.0, speed_rating=68, passing_rating=81, defending_rating=86, shooting_rating=76),
        Player("mun_16", "Amad Diallo", 16, "manchester_united", "RW", x(60.0), 18.0, speed_rating=87, passing_rating=80, defending_rating=50, shooting_rating=78),
        Player("mun_08", "Bruno Fernandes", 8, "manchester_united", "CAM", x(48.0), 50.0, speed_rating=76, passing_rating=90, defending_rating=68, shooting_rating=86),
        Player("mun_10", "Marcus Rashford", 10, "manchester_united", "LW", x(60.0), 82.0, speed_rating=89, passing_rating=78, defending_rating=48, shooting_rating=83),
        Player("mun_11", "Joshua Zirkzee", 11, "manchester_united", "ST", x(64.0), 50.0, speed_rating=79, passing_rating=80, defending_rating=52, shooting_rating=80),
    ]
    return Team(
        team_id="manchester_united",
        name="Manchester United",
        short_name="MUN",
        primary_color="#DA291C",
        secondary_color="#FBE122",
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
        "home_factory": create_manchester_city,
        "away_factory": create_arsenal,
    },
    {
        "id": "epl_liv_che",
        "title": "Liverpool vs. Chelsea",
        "home": "liverpool",
        "away": "chelsea",
        "home_factory": create_liverpool,
        "away_factory": create_chelsea,
    },
    {
        "id": "epl_tot_mun",
        "title": "Tottenham Hotspur vs. Manchester United",
        "home": "tottenham",
        "away": "manchester_united",
        "home_factory": create_tottenham,
        "away_factory": create_manchester_united,
    },
]


def build_matchup(matchup_id: str) -> tuple[Team, Team]:
    """Retrieve home and away team instances for the chosen matchup."""
    for item in AVAILABLE_MATCHUPS:
        if item["id"] == matchup_id:
            return item["home_factory"](direction=1), item["away_factory"](direction=-1)
    # Default to Manchester City vs Arsenal
    return create_manchester_city(direction=1), create_arsenal(direction=-1)
