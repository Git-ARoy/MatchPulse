"""Rules, set-piece setups, fouls, and card arbitration for the simulation."""

from __future__ import annotations

import random
from .models import Ball, BallState, Player, SetPieceType, Team, Vector2D
from .physics import GOAL_Y_MAX, GOAL_Y_MIN


def is_inside_penalty_box(x: float, y: float, box_team_dir: int) -> bool:
    """Check if coordinates fall inside the penalty box defending the goal of box_team_dir."""
    # If box_team_dir == 1: defending goal at x=0 -> box is x in [0, 16.5], y in [20.0, 80.0]
    # If box_team_dir == -1: defending goal at x=100 -> box is x in [83.5, 100.0], y in [20.0, 80.0]
    if 20.0 <= y <= 80.0:
        if box_team_dir == 1 and x <= 16.5:
            return True
        if box_team_dir == -1 and x >= 83.5:
            return True
    return False


def setup_kickoff(home_team: Team, away_team: Team, ball: Ball, kicking_team: Team) -> None:
    """Position teams and ball for kick-off."""
    ball.x = 50.0
    ball.y = 50.0
    ball.z = 0.0
    ball.vx = 0.0
    ball.vy = 0.0
    ball.vz = 0.0
    ball.speed_kph = 0.0
    ball.state = BallState.set_piece

    # Reset all player positions back to formation anchors
    for team in (home_team, away_team):
        for player in team.players:
            if player.is_sent_off:
                continue
            player.x = player.base_x
            player.y = player.base_y
            player.vx = 0.0
            player.vy = 0.0

    # Ensure striker of kicking team is at center spot
    striker = None
    for p in kicking_team.players:
        if p.role == "ST" and not p.is_sent_off:
            striker = p
            break
    if not striker:
        striker = kicking_team.active_players[-1]

    striker.x = 50.0 + (0.5 if kicking_team.attacking_direction == 1 else -0.5)
    striker.y = 50.0
    ball.carrier_id = striker.player_id
    ball.last_touch_team_id = kicking_team.team_id
    ball.last_touch_player_id = striker.player_id


def setup_penalty(
    foul_x: float,
    foul_y: float,
    attacking_team: Team,
    defending_team: Team,
    ball: Ball,
) -> Player:
    """Position all players and ball for a penalty kick."""
    # Penalty spot: x = 88.5 if attacking towards x=100, x = 11.5 if attacking towards x=0
    target_spot_x = 88.5 if attacking_team.attacking_direction == 1 else 11.5
    goal_x = 99.0 if attacking_team.attacking_direction == 1 else 1.0

    ball.x = target_spot_x
    ball.y = 50.0
    ball.z = 0.0
    ball.vx = 0.0
    ball.vy = 0.0
    ball.speed_kph = 0.0
    ball.state = BallState.set_piece

    # Clear all outfield players outside the 18-yard box and D-arc (behind x=80 or x=20)
    clear_x_home = 78.0 if attacking_team.attacking_direction == 1 else 22.0
    spread_y = 20.0
    for team in (attacking_team, defending_team):
        for p in team.players:
            if p.is_sent_off:
                continue
            if p.role == "GK" and p.team_id == defending_team.team_id:
                # Goalkeeper on the goal line
                p.x = goal_x
                p.y = 50.0
            else:
                p.x = clear_x_home + random.uniform(-4.0, 4.0)
                p.y = spread_y
                spread_y = (spread_y + 6.5) % 80.0 + 10.0

    # Choose best penalty taker (highest shooting rating striker or attacking midfielder)
    candidates = [p for p in attacking_team.active_players if p.role in ("ST", "LW", "RW", "CAM", "CM")]
    taker = max(candidates or attacking_team.active_players, key=lambda p: p.shooting_rating)
    taker.x = target_spot_x - (2.0 if attacking_team.attacking_direction == 1 else -2.0)
    taker.y = 50.0

    ball.carrier_id = taker.player_id
    ball.last_touch_team_id = attacking_team.team_id
    ball.last_touch_player_id = taker.player_id
    return taker


def setup_free_kick(
    foul_x: float,
    foul_y: float,
    attacking_team: Team,
    defending_team: Team,
    ball: Ball,
) -> tuple[Player, list[Player]]:
    """Position free-kick taker and defending wall."""
    ball.x = foul_x
    ball.y = foul_y
    ball.z = 0.0
    ball.vx = 0.0
    ball.vy = 0.0
    ball.speed_kph = 0.0
    ball.state = BallState.set_piece

    # Select taker
    taker = max(attacking_team.active_players, key=lambda p: p.passing_rating + p.shooting_rating)
    taker.x = foul_x - (1.5 if attacking_team.attacking_direction == 1 else -1.5)
    taker.y = foul_y
    ball.carrier_id = taker.player_id
    ball.last_touch_team_id = attacking_team.team_id
    ball.last_touch_player_id = taker.player_id

    # Form a 3-man defending wall 9.15m away towards goal
    goal_x = 99.0 if attacking_team.attacking_direction == 1 else 1.0
    wall_dir = Vector2D(goal_x - foul_x, 50.0 - foul_y).normalized()
    wall_pos = Vector2D(foul_x, foul_y) + wall_dir * 9.15

    wall_candidates = [p for p in defending_team.active_players if p.role in ("CB", "CDM", "CM", "ST")]
    wall_players = wall_candidates[:3]
    for i, p in enumerate(wall_players):
        offset = (i - 1) * 1.8
        p.x = wall_pos.x
        p.y = max(10.0, min(90.0, wall_pos.y + offset))

    return taker, wall_players


def setup_corner(
    corner_x: float,
    corner_y: float,
    attacking_team: Team,
    defending_team: Team,
    ball: Ball,
) -> Player:
    """Position corner taker and box attackers/defenders."""
    ball.x = corner_x
    ball.y = corner_y
    ball.z = 0.0
    ball.vx = 0.0
    ball.vy = 0.0
    ball.speed_kph = 0.0
    ball.state = BallState.set_piece

    taker = max(attacking_team.active_players, key=lambda p: p.passing_rating)
    taker.x = corner_x
    taker.y = corner_y
    ball.carrier_id = taker.player_id
    ball.last_touch_team_id = attacking_team.team_id
    ball.last_touch_player_id = taker.player_id

    # Crowd the penalty box
    box_x = 90.0 if attacking_team.attacking_direction == 1 else 10.0
    for p in attacking_team.active_players:
        if p.player_id == taker.player_id or p.role == "GK":
            continue
        p.x = box_x + random.uniform(-6.0, 4.0)
        p.y = random.uniform(35.0, 65.0)

    for p in defending_team.active_players:
        if p.role == "GK":
            p.x = 98.5 if attacking_team.attacking_direction == 1 else 1.5
            p.y = 50.0
        else:
            p.x = box_x + random.uniform(-4.0, 6.0)
            p.y = random.uniform(32.0, 68.0)

    return taker
