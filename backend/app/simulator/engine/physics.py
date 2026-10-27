"""Kinematics, collision detection, and ball physics for match simulation."""

from __future__ import annotations

import math
from .models import Ball, BallState, Player, Team, Vector2D

PITCH_WIDTH_M = 105.0  # standard Premier League pitch length (X axis in normalized units)
PITCH_HEIGHT_M = 68.0  # standard Premier League pitch width (Y axis in normalized units)

# Goal mouth in normalized pitch coordinates:
# Goal width is 7.32m -> 7.32 / 68.0 * 100 ~= 10.76% of pitch height
GOAL_Y_MIN = 44.62
GOAL_Y_MAX = 55.38


def update_player_motion(
    player: Player,
    target: Vector2D,
    delta_t: float,
    all_players: list[Player],
) -> None:
    """Move player towards target position with realistic acceleration and speed."""
    if player.is_sent_off:
        return

    current = player.pos
    dist = current.distance_to(target)

    # Max speed: ~26 km/h to ~34 km/h depending on rating
    # 30 km/h = 8.33 m/s -> on 105m pitch = ~7.93% per second
    max_speed_units_per_sec = 6.0 + (player.speed_rating / 100.0) * 4.5

    if dist > 0.3:
        direction = (target - current).normalized()
        step = min(dist, max_speed_units_per_sec * delta_t)
        player.vx = direction.x * max_speed_units_per_sec
        player.vy = direction.y * max_speed_units_per_sec
        new_pos = current + direction * step
    else:
        player.vx = 0.0
        player.vy = 0.0
        new_pos = current

    # Separation: slight pushback if too close to another player
    for other in all_players:
        if other.player_id == player.player_id or other.is_sent_off:
            continue
        separation_dist = new_pos.distance_to(other.pos)
        if 0 < separation_dist < 1.8:
            push = (new_pos - other.pos).normalized() * (1.8 - separation_dist) * 0.5
            new_pos = new_pos + push

    # Contain within field bounds
    player.pos = new_pos.clamp(1.0, 99.0, 1.0, 99.0)


def update_ball_physics(ball: Ball, delta_t: float) -> None:
    """Update ball position, deceleration, height arc, and speed."""
    if ball.state == BallState.controlled:
        ball.vx = 0.0
        ball.vy = 0.0
        ball.vz = 0.0
        ball.z = 0.0
        ball.speed_kph = 0.0
        return

    # Ball in motion (ground pass, shot, loose)
    ball.x += ball.vx * delta_t
    ball.y += ball.vy * delta_t

    # Ground friction deceleration
    friction = 0.88 if ball.state == BallState.ground_pass else 0.94
    ball.vx *= (friction ** (delta_t * 10))
    ball.vy *= (friction ** (delta_t * 10))

    # Calculate current speed in km/h
    # 1 unit/sec ~= 1.05 m/s = 3.78 km/h
    units_per_sec = math.hypot(ball.vx, ball.vy)
    ball.speed_kph = units_per_sec * 3.78

    # Lofted ball height physics
    if ball.state == BallState.lofted_pass:
        ball.z += ball.vz * delta_t
        ball.vz -= 9.8 * delta_t  # gravity
        if ball.z <= 0.0:
            ball.z = 0.0
            ball.vz = 0.0
            ball.state = BallState.ground_pass

    # Stop ball if moving very slowly
    if units_per_sec < 0.4 and ball.state not in (BallState.set_piece, BallState.out_of_bounds):
        ball.vx = 0.0
        ball.vy = 0.0
        ball.speed_kph = 0.0
        ball.state = BallState.loose
