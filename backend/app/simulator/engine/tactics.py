"""Tactical shape, zones, and formation positioning algorithms."""

from __future__ import annotations

from .models import Player, Team, Vector2D


def get_zone_for_team(x: float, y: float, attacking_direction: int) -> str:
    """Determine the canonical zone for the team currently in possession."""
    # Penalty boxes (16.5m depth from goal line, width 40.3m -> roughly y between 20 and 80)
    if (attacking_direction == 1 and x >= 83.5 and 20.0 <= y <= 80.0) or \
       (attacking_direction == -1 and x <= 16.5 and 20.0 <= y <= 80.0):
        return "penalty_box"

    # From attacking perspective:
    # If attacking_direction == 1 (attacking towards x=100):
    #   x < 33.3 -> defensive_third
    #   33.3 <= x < 66.6 -> middle_third
    #   x >= 66.6 -> attacking_third
    # If attacking_direction == -1 (attacking towards x=0):
    #   x > 66.6 -> defensive_third
    #   33.3 <= x <= 66.6 -> middle_third
    #   x < 33.3 -> attacking_third
    rel_x = x if attacking_direction == 1 else 100.0 - x
    if rel_x < 33.3:
        return "defensive_third"
    elif rel_x < 66.6:
        return "middle_third"
    return "attacking_third"


def compute_tactical_target(
    player: Player,
    team: Team,
    ball_pos: Vector2D,
    in_possession: bool,
    opp_team: Team,
) -> Vector2D:
    """Compute the desired tactical target position for a player on the pitch."""
    # Base anchor
    base = Vector2D(player.base_x, player.base_y)
    dir_factor = team.attacking_direction

    # Goalkeeper behavior
    if player.role == "GK":
        goal_x = 3.5 if dir_factor == 1 else 96.5
        # Sweeper keeper moves out slightly when ball is far
        ball_distance = abs(ball_pos.x - goal_x)
        advance = min(12.0, ball_distance * 0.15) * (1 if dir_factor == 1 else -1)
        # Shift Y towards ball Y to narrow the angle
        clamped_y = max(38.0, min(62.0, 50.0 + (ball_pos.y - 50.0) * 0.35))
        return Vector2D(goal_x + advance, clamped_y)

    # Outfield players:
    # 1. Team block shift based on ball X position
    # If in possession, team pushes forward; if defending, team drops back
    ball_shift_x = (ball_pos.x - 50.0) * 0.45
    possession_advance = (12.0 * dir_factor) if in_possession else (-8.0 * dir_factor)
    target_x = base.x + ball_shift_x + possession_advance

    # 2. Width adjustments
    # Attackers spread wide, defenders stay compact
    target_y = base.y
    if in_possession:
        if player.role in ("LW", "RW", "LB", "RB"):
            # Spread towards wings
            target_y = base.y + (8.0 if base.y > 50.0 else -8.0)
    else:
        # Defending compactness: squeeze towards center line (y=50)
        target_y = 50.0 + (base.y - 50.0) * 0.75

    # 3. Ball attraction for midfielders / pressing players
    dist_to_ball = base.distance_to(ball_pos)
    if not in_possession:
        # If player is near ball and has defensive role, press towards ball
        if player.role in ("CDM", "CM", "CB", "LB", "RB") and dist_to_ball < 22.0:
            press_vector = (ball_pos - base).normalized() * min(10.0, 22.0 - dist_to_ball)
            target_x += press_vector.x
            target_y += press_vector.y
    else:
        # If in possession and nearby, offer passing angle
        if player.role in ("CM", "CAM", "LW", "RW", "ST") and dist_to_ball < 25.0:
            target_x += (ball_pos.x - target_x) * 0.25

    # Clamp target within pitch bounds
    # Keep defenders roughly in their own half/third, forwards in attacking zones
    min_x = 10.0 if dir_factor == 1 else 2.0
    max_x = 98.0 if dir_factor == 1 else 90.0
    return Vector2D(
        max(min_x, min(max_x, target_x)),
        max(4.0, min(96.0, target_y)),
    )
