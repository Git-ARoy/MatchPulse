"""Autonomous, physics-informed 90-minute football match simulation engine."""

from __future__ import annotations

import math
import random
import uuid
from datetime import UTC, datetime
from typing import Any, Callable

from .models import Ball, BallState, MatchPhase, Player, SetPieceType, Team, Vector2D
from .physics import (
    GOAL_Y_MAX,
    GOAL_Y_MIN,
    update_ball_physics,
    update_player_motion,
)
from .rosters import build_matchup
from .rules import (
    is_inside_penalty_box,
    setup_corner,
    setup_free_kick,
    setup_kickoff,
    setup_penalty,
)
from .tactics import compute_tactical_target, get_zone_for_team


class MatchSimulation:
    """Orchestrates an entire 90-minute football match with continuous physics,
    tactical AI, rules enforcement, and canonical event streaming.
    """

    def __init__(
        self,
        match_id: str = "epl_mci_ars",
        matchup_id: str = "epl_mci_ars",
        event_callback: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        self.match_id = match_id
        self.matchup_id = matchup_id
        self.event_callback = event_callback

        self.home_team, self.away_team = build_matchup(matchup_id)
        self.ball = Ball()

        # Clock & State
        self.phase = MatchPhase.not_started
        self.minute = 0
        self.second = 0
        self.stoppage_minutes = 2
        self.is_stoppage = False
        self.is_paused = True
        self.speed_multiplier = 1.0  # 1.0 = real-time (1s wall = 1s match)
        self.total_match_seconds = 0.0

        # Bookkeeping
        self.event_counter = 0
        self.last_event_clock_seconds = -1
        self.recent_events: list[dict[str, Any]] = []

        # Tactical state tracking
        self.possession_team: Team = self.home_team
        self.active_set_piece: SetPieceType = SetPieceType.none
        self.set_piece_timer: float = 0.0
        self.pass_target_player: Player | None = None
        self.cooldown_events: dict[str, float] = {}

        # Tracking entries for zones to avoid spamming third entries
        self.in_attacking_third = False
        self.in_penalty_box = False

    @property
    def all_players(self) -> list[Player]:
        return self.home_team.players + self.away_team.players

    @property
    def defending_team(self) -> Team:
        return self.away_team if self.possession_team.team_id == self.home_team.team_id else self.home_team

    def start(self) -> None:
        """Start or unpause the match."""
        if self.phase == MatchPhase.not_started:
            self.phase = MatchPhase.first_half
            self.minute = 0
            self.second = 0
            self.total_match_seconds = 0.0
            setup_kickoff(self.home_team, self.away_team, self.ball, self.home_team)
            self._emit_event("kickoff", self.home_team.team_id, self.ball.carrier_id, 50.0, 50.0, "middle_third")
        self.is_paused = False

    def pause(self) -> None:
        self.is_paused = True

    def resume(self) -> None:
        self.is_paused = False

    def reset(self, matchup_id: str | None = None) -> None:
        """Reset match to minute 00:00."""
        if matchup_id:
            self.matchup_id = matchup_id
        self.home_team, self.away_team = build_matchup(self.matchup_id)
        self.ball = Ball()
        self.phase = MatchPhase.not_started
        self.minute = 0
        self.second = 0
        self.total_match_seconds = 0.0
        self.is_paused = True
        self.event_counter = 0
        self.last_event_clock_seconds = -1
        self.recent_events.clear()
        self.active_set_piece = SetPieceType.none
        self.set_piece_timer = 0.0
        self.in_attacking_third = False
        self.in_penalty_box = False

    def set_speed(self, multiplier: float) -> None:
        self.speed_multiplier = max(0.5, min(120.0, multiplier))

    def step(self, delta_t: float) -> None:
        """Advance the simulation by delta_t match seconds."""
        if self.is_paused or self.phase in (MatchPhase.not_started, MatchPhase.half_time, MatchPhase.full_time):
            return

        effective_dt = delta_t * self.speed_multiplier
        self.total_match_seconds += effective_dt
        self.minute = int(self.total_match_seconds // 60)
        self.second = int(self.total_match_seconds % 60)

        # Check half time & full time transitions
        if self.phase == MatchPhase.first_half and self.minute >= (45 + self.stoppage_minutes):
            self.phase = MatchPhase.half_time
            self._emit_event("half_time", self.home_team.team_id, None, 50.0, 50.0, "middle_third")
            return

        if self.phase == MatchPhase.second_half and self.minute >= (90 + self.stoppage_minutes):
            self.phase = MatchPhase.full_time
            self._emit_event("full_time", self.home_team.team_id, None, 50.0, 50.0, "middle_third")
            return

        # 1. Set piece execution delay handling
        if self.active_set_piece != SetPieceType.none:
            self.set_piece_timer += effective_dt
            if self.set_piece_timer >= 2.0:  # 2 second pause before taking set piece
                self._execute_active_set_piece()
            self._update_all_player_positions(effective_dt)
            return

        # 2. Physics & Motion updates
        update_ball_physics(self.ball, effective_dt)
        self._update_all_player_positions(effective_dt)

        # 3. Ball carrier / Loose ball resolution
        self._resolve_ball_interaction(effective_dt)

        # 4. Out of bounds & goal line checks
        self._check_pitch_boundaries()

    def advance_half_time(self) -> None:
        """Advance from half time into the second half."""
        if self.phase == MatchPhase.half_time:
            self.phase = MatchPhase.second_half
            self.total_match_seconds = 45 * 60
            self.minute = 45
            self.second = 0
            # Switch sides
            self.home_team.attacking_direction = -1
            self.away_team.attacking_direction = 1
            # Reset formation anchors for second half
            for t in (self.home_team, self.away_team):
                for p in t.players:
                    p.base_x = 100.0 - p.base_x
            setup_kickoff(self.home_team, self.away_team, self.ball, self.away_team)
            self._emit_event("kickoff", self.away_team.team_id, self.ball.carrier_id, 50.0, 50.0, "middle_third")
            self.is_paused = False

    # -------------------------------------------------------------------------
    # Player AI and Ball Decisions
    # -------------------------------------------------------------------------

    def _update_all_player_positions(self, delta_t: float) -> None:
        ball_pos = self.ball.pos
        all_players = self.all_players

        for team in (self.home_team, self.away_team):
            in_possession = (team.team_id == self.possession_team.team_id)
            opp_team = self.away_team if in_possession else self.home_team

            for player in team.players:
                if player.is_sent_off:
                    continue
                # If player is carrying the ball, player steers towards goal / open space
                if self.ball.state == BallState.controlled and player.player_id == self.ball.carrier_id:
                    target = self._compute_carrier_target(player, team)
                else:
                    target = compute_tactical_target(player, team, ball_pos, in_possession, opp_team)

                update_player_motion(player, target, delta_t, all_players)

    def _compute_carrier_target(self, carrier: Player, team: Team) -> Vector2D:
        """Ball carrier advances towards opponent goal with width variation."""
        goal_x = 98.0 if team.attacking_direction == 1 else 2.0
        # Check defenders in front
        return Vector2D(goal_x, carrier.y + random.uniform(-2.0, 2.0))

    def _resolve_ball_interaction(self, delta_t: float) -> None:
        """Handle player with ball actions, or players contesting a loose ball."""
        carrier = self._get_player_by_id(self.ball.carrier_id) if self.ball.carrier_id else None

        if carrier is not None and self.ball.state == BallState.controlled:
            # Sync ball position to carrier's feet
            dir_factor = self.possession_team.attacking_direction
            self.ball.x = carrier.x + 0.6 * dir_factor
            self.ball.y = carrier.y

            # Zone entry checks
            zone = get_zone_for_team(carrier.x, carrier.y, dir_factor)
            if zone == "attacking_third" and not self.in_attacking_third:
                self.in_attacking_third = True
                self._emit_event("attacking_third_entry", carrier.team_id, carrier.player_id, carrier.x, carrier.y, zone)
            elif zone != "attacking_third":
                self.in_attacking_third = False

            if zone == "penalty_box" and not self.in_penalty_box:
                self.in_penalty_box = True
                self._emit_event("penalty_box_entry", carrier.team_id, carrier.player_id, carrier.x, carrier.y, zone)
            elif zone != "penalty_box":
                self.in_penalty_box = False

            # Carrier decision cycle
            carrier.cooldown_ticks += 1
            if carrier.cooldown_ticks >= 8:  # decide action every ~0.8s
                carrier.cooldown_ticks = 0
                self._carrier_action_decision(carrier)

            # Defensive pressure & tackles
            self._evaluate_defensive_pressure(carrier)

        elif self.ball.state in (BallState.ground_pass, BallState.lofted_pass, BallState.loose):
            # Check if any player intercepts or receives the ball
            self._evaluate_ball_recovery()

    def _carrier_action_decision(self, carrier: Player) -> None:
        """Ball carrier decides: pass, shoot, or continue dribbling."""
        dir_factor = self.possession_team.attacking_direction
        rel_x = carrier.x if dir_factor == 1 else 100.0 - carrier.x
        zone = get_zone_for_team(carrier.x, carrier.y, dir_factor)

        # 1. SHOOTING CHANCE: In attacking third / box with shooting opportunity
        if (rel_x >= 75.0 and random.random() < 0.28) or (zone == "penalty_box" and random.random() < 0.65):
            self._execute_shot(carrier)
            return

        # 2. PASSING CHANCE: Scan for open teammates
        teammates = [
            p for p in self.possession_team.active_players
            if p.player_id != carrier.player_id and p.role != "GK"
        ]
        if teammates and random.random() < 0.72:
            # Pick a teammate in good forward/support position
            best_target = self._select_pass_target(carrier, teammates, dir_factor)
            if best_target:
                self._execute_pass(carrier, best_target)
                return

        # 3. DRIBBLE: Carrier holds ball and advances
        pass

    def _select_pass_target(self, carrier: Player, teammates: list[Player], dir_factor: int) -> Player:
        """Score potential recipients based on forward position and passing lane openness."""
        scored = []
        for p in teammates:
            # Forward gain
            forward_progression = (p.x - carrier.x) * dir_factor
            dist = carrier.pos.distance_to(p.pos)
            if dist > 45.0 or dist < 4.0:
                continue

            # Check if defender is blocking pass lane
            opp_blockers = sum(
                1 for opp in self.defending_team.active_players
                if opp.pos.distance_to(p.pos) < 4.0
            )
            score = forward_progression * 1.5 - opp_blockers * 6.0 + random.uniform(-2.0, 5.0)
            scored.append((score, p))

        if scored:
            scored.sort(key=lambda item: item[0], reverse=True)
            return scored[0][1]
        return random.choice(teammates)

    def _execute_pass(self, passer: Player, receiver: Player) -> None:
        """Initiate ground or lofted pass towards receiver."""
        dist = passer.pos.distance_to(receiver.pos)
        distance_m = dist * 1.05  # approx meters
        pass_direction = (receiver.pos - passer.pos).normalized()

        # Pass speed: 35 to 65 km/h
        speed_units_per_sec = 12.0 + (passer.passing_rating / 100.0) * 6.0
        self.ball.vx = pass_direction.x * speed_units_per_sec
        self.ball.vy = pass_direction.y * speed_units_per_sec
        self.ball.carrier_id = None
        self.ball.state = BallState.ground_pass if distance_m < 25.0 else BallState.lofted_pass
        if self.ball.state == BallState.lofted_pass:
            self.ball.vz = 4.5

        self.ball.last_touch_team_id = passer.team_id
        self.ball.last_touch_player_id = passer.player_id
        self.pass_target_player = receiver

        # Determine completion likelihood based on passer rating vs distance
        diff_rating = min(100.0, max(10.0, distance_m * 1.8 + (100.0 - passer.passing_rating) * 0.4))
        completed = random.random() < (passer.passing_rating / 115.0)

        zone = get_zone_for_team(passer.x, passer.y, self.possession_team.attacking_direction)
        self._emit_event(
            "pass",
            passer.team_id,
            passer.player_id,
            passer.x,
            passer.y,
            zone,
            {
                "completed": completed,
                "recipient_player_id": receiver.player_id,
                "distance_m": round(distance_m, 1),
                "difficulty_rating": round(diff_rating, 1),
            },
        )

    def _execute_shot(self, shooter: Player) -> None:
        """Take a shot on goal."""
        dir_factor = self.possession_team.attacking_direction
        goal_x = 100.0 if dir_factor == 1 else 0.0
        goal_y = random.uniform(GOAL_Y_MIN + 1.0, GOAL_Y_MAX - 1.0)
        shot_vector = (Vector2D(goal_x, goal_y) - shooter.pos).normalized()

        shot_speed_kph = 70.0 + (shooter.shooting_rating / 100.0) * 45.0 + random.uniform(-5.0, 10.0)
        units_per_sec = shot_speed_kph / 3.78

        self.ball.vx = shot_vector.x * units_per_sec
        self.ball.vy = shot_vector.y * units_per_sec
        self.ball.carrier_id = None
        self.ball.state = BallState.shot
        self.ball.last_touch_team_id = shooter.team_id
        self.ball.last_touch_player_id = shooter.player_id

        # Shot outcome calculation
        opp_gk = [p for p in self.defending_team.players if p.role == "GK"][0]
        on_target = random.random() < (shooter.shooting_rating / 110.0)

        zone = get_zone_for_team(shooter.x, shooter.y, dir_factor)

        if not on_target:
            outcome = "off_target"
            self._emit_event(
                "shot", shooter.team_id, shooter.player_id, shooter.x, shooter.y, zone,
                {"on_target": False, "outcome": "off_target", "speed_kph": round(shot_speed_kph, 1)},
            )
        else:
            # On target shot: Can GK save it?
            save_probability = (opp_gk.defending_rating / 120.0) - (shooter.shooting_rating / 250.0)
            if random.random() < save_probability:
                outcome = "saved"
                self._emit_event(
                    "shot", shooter.team_id, shooter.player_id, shooter.x, shooter.y, zone,
                    {"on_target": True, "outcome": "saved", "speed_kph": round(shot_speed_kph, 1)},
                )
            else:
                outcome = "goal"
                self._emit_event(
                    "shot", shooter.team_id, shooter.player_id, shooter.x, shooter.y, zone,
                    {"on_target": True, "outcome": "goal", "speed_kph": round(shot_speed_kph, 1)},
                )
                self._score_goal(shooter, shot_speed_kph)

    def _score_goal(self, scorer: Player, speed_kph: float) -> None:
        """Award goal, update score, celebrate, and reset to kickoff."""
        self.possession_team.score += 1
        zone = get_zone_for_team(scorer.x, scorer.y, self.possession_team.attacking_direction)

        self._emit_event(
            "goal", scorer.team_id, scorer.player_id, scorer.x, scorer.y, zone,
            {"outcome": "goal", "on_target": True, "speed_kph": round(speed_kph, 1)},
        )

        # Kickoff for conceded team
        conceding_team = self.defending_team
        self.possession_team = conceding_team
        setup_kickoff(self.home_team, self.away_team, self.ball, conceding_team)
        self.active_set_piece = SetPieceType.kickoff
        self.set_piece_timer = 0.0

    def _evaluate_defensive_pressure(self, carrier: Player) -> None:
        """Defenders near ball carrier attempt tackles, interceptions, or commit fouls."""
        dir_factor = self.possession_team.attacking_direction
        carrier_pos = carrier.pos

        # Check nearby defenders within 2.5m
        nearby_defenders = [
            d for d in self.defending_team.active_players
            if d.pos.distance_to(carrier_pos) < 2.8
        ]

        # Pressure intensity event if in attacking third with 2+ defenders
        if len(nearby_defenders) >= 2 and carrier.pos.distance_to(Vector2D(100.0 if dir_factor == 1 else 0.0, 50.0)) < 35.0:
            if self._event_cooldown_ok("pressure_event", 12.0):
                zone = get_zone_for_team(carrier.x, carrier.y, dir_factor)
                self._emit_event("pressure_event", self.defending_team.team_id, nearby_defenders[0].player_id, carrier.x, carrier.y, zone, {"intensity": 84.0})

        if not nearby_defenders:
            return

        tackler = nearby_defenders[0]

        # Tackle contest
        tackle_prob = (tackler.defending_rating / 140.0) + (tackler.aggression_rating / 300.0)
        foul_prob = (tackler.aggression_rating / 100.0) * 0.22

        if random.random() < 0.15:  # tackle attempt window
            if random.random() < foul_prob:
                self._handle_foul(tackler, carrier)
            elif random.random() < tackle_prob:
                # Successful tackle / regain
                zone = get_zone_for_team(tackler.x, tackler.y, self.defending_team.attacking_direction)
                self._emit_event("tackle", tackler.team_id, tackler.player_id, tackler.x, tackler.y, zone)

                # Check high regain (won in opposition half)
                in_opp_half = (tackler.x > 50.0 if self.defending_team.attacking_direction == 1 else tackler.x < 50.0)
                if in_opp_half:
                    self._emit_event("high_regain", tackler.team_id, tackler.player_id, tackler.x, tackler.y, zone)

                # Turn over possession
                self.possession_team = self.defending_team
                self.ball.carrier_id = tackler.player_id
                self.ball.state = BallState.controlled
                self.ball.last_touch_team_id = tackler.team_id
                self.ball.last_touch_player_id = tackler.player_id

    def _handle_foul(self, fouler: Player, victim: Player) -> None:
        """Arbitrate foul, penalty or free kick, and cards."""
        foul_x = victim.x
        foul_y = victim.y
        fouling_team_dir = self.defending_team.attacking_direction
        victim_team_dir = self.possession_team.attacking_direction
        zone = get_zone_for_team(foul_x, foul_y, victim_team_dir)

        self._emit_event("foul", fouler.team_id, fouler.player_id, foul_x, foul_y, zone)

        # Card evaluation
        if random.random() < (fouler.aggression_rating / 100.0) * 0.45:
            fouler.yellow_cards += 1
            if fouler.yellow_cards == 1:
                self._emit_event("yellow_card", fouler.team_id, fouler.player_id, foul_x, foul_y, zone)
            else:
                fouler.is_sent_off = True
                self._emit_event("red_card", fouler.team_id, fouler.player_id, foul_x, foul_y, zone)

        # Is foul inside penalty box defending fouler's goal?
        in_box = is_inside_penalty_box(foul_x, foul_y, fouling_team_dir)
        if in_box:
            # AWARD PENALTY!
            setup_penalty(foul_x, foul_y, self.possession_team, self.defending_team, self.ball)
            self.active_set_piece = SetPieceType.penalty
            self.set_piece_timer = 0.0
        else:
            # AWARD FREE KICK
            setup_free_kick(foul_x, foul_y, self.possession_team, self.defending_team, self.ball)
            self.active_set_piece = SetPieceType.free_kick
            self.set_piece_timer = 0.0
            self._emit_event("free_kick", self.possession_team.team_id, self.ball.carrier_id, foul_x, foul_y, zone)

    def _execute_active_set_piece(self) -> None:
        """Carry out the set piece once players are set."""
        set_piece = self.active_set_piece
        self.active_set_piece = SetPieceType.none
        self.set_piece_timer = 0.0

        if set_piece == SetPieceType.kickoff:
            striker = self._get_player_by_id(self.ball.carrier_id)
            if striker:
                # Pass back to central midfielder
                midfielder = next((p for p in self.possession_team.active_players if p.role in ("CM", "CDM")), self.possession_team.active_players[0])
                self._execute_pass(striker, midfielder)

        elif set_piece == SetPieceType.penalty:
            taker = self._get_player_by_id(self.ball.carrier_id)
            if taker:
                self._execute_shot(taker)

        elif set_piece == SetPieceType.free_kick:
            taker = self._get_player_by_id(self.ball.carrier_id)
            if taker:
                dir_factor = self.possession_team.attacking_direction
                rel_x = taker.x if dir_factor == 1 else 100.0 - taker.x
                if rel_x >= 75.0:
                    # Shoot directly at goal
                    self._execute_shot(taker)
                else:
                    # Cross or pass into open teammate
                    teammates = [p for p in self.possession_team.active_players if p.player_id != taker.player_id and p.role != "GK"]
                    if teammates:
                        target = random.choice(teammates)
                        self._execute_pass(taker, target)

        elif set_piece == SetPieceType.corner:
            taker = self._get_player_by_id(self.ball.carrier_id)
            if taker:
                # Curl cross into penalty box
                zone = get_zone_for_team(taker.x, taker.y, self.possession_team.attacking_direction)
                self._emit_event("corner", self.possession_team.team_id, taker.player_id, taker.x, taker.y, zone)
                # Cross into central box
                box_x = 90.0 if self.possession_team.attacking_direction == 1 else 10.0
                cross_target = Vector2D(box_x, 50.0 + random.uniform(-10.0, 10.0))
                cross_dir = (cross_target - taker.pos).normalized()
                self.ball.vx = cross_dir.x * 16.0
                self.ball.vy = cross_dir.y * 16.0
                self.ball.vz = 5.0
                self.ball.carrier_id = None
                self.ball.state = BallState.lofted_pass

    def _evaluate_ball_recovery(self) -> None:
        """Check if passing target or any nearby player reaches the loose / in-transit ball."""
        ball_pos = self.ball.pos

        # Check intended pass receiver first
        if self.pass_target_player and not self.pass_target_player.is_sent_off:
            if self.pass_target_player.pos.distance_to(ball_pos) < 2.0:
                self.ball.carrier_id = self.pass_target_player.player_id
                self.ball.state = BallState.controlled
                self.pass_target_player = None
                return

        # Check all other active players
        closest_player = None
        min_dist = 2.2
        for p in self.all_players:
            if p.is_sent_off:
                continue
            dist = p.pos.distance_to(ball_pos)
            if dist < min_dist:
                min_dist = dist
                closest_player = p

        if closest_player:
            # Ball controlled
            prev_team_id = self.possession_team.team_id
            new_team = self.home_team if closest_player.team_id == self.home_team.team_id else self.away_team
            self.possession_team = new_team
            self.ball.carrier_id = closest_player.player_id
            self.ball.state = BallState.controlled
            self.ball.last_touch_team_id = closest_player.team_id
            self.ball.last_touch_player_id = closest_player.player_id
            self.pass_target_player = None

            # If turnover occurred, emit interception
            if prev_team_id != new_team.team_id:
                zone = get_zone_for_team(closest_player.x, closest_player.y, new_team.attacking_direction)
                self._emit_event("interception", new_team.team_id, closest_player.player_id, closest_player.x, closest_player.y, zone)

    def _check_pitch_boundaries(self) -> None:
        """Check if ball went out over touchline or goal lines."""
        bx, by = self.ball.x, self.ball.y

        # Touchlines (throw-in)
        if by <= 0.0 or by >= 100.0:
            clamped_y = 0.0 if by <= 0.0 else 100.0
            throwing_team = self.defending_team if self.ball.last_touch_team_id == self.possession_team.team_id else self.possession_team
            taker = min(throwing_team.active_players, key=lambda p: abs(p.y - clamped_y) + abs(p.x - bx))
            self.ball.x = max(2.0, min(98.0, bx))
            self.ball.y = clamped_y
            self.ball.carrier_id = taker.player_id
            self.ball.state = BallState.controlled
            self.possession_team = throwing_team
            zone = get_zone_for_team(self.ball.x, self.ball.y, throwing_team.attacking_direction)
            self._emit_event("throw_in", throwing_team.team_id, taker.player_id, self.ball.x, self.ball.y, zone)
            return

        # Goal lines (x <= 0 or x >= 100)
        if bx <= 0.0 or bx >= 100.0:
            # Between goal posts?
            if GOAL_Y_MIN <= by <= GOAL_Y_MAX:
                # Goal scored!
                scoring_team = self.home_team if bx >= 100.0 else self.away_team
                scorer = self._get_player_by_id(self.ball.last_touch_player_id) or scoring_team.active_players[-1]
                self._score_goal(scorer, self.ball.speed_kph or 85.0)
                return

            # Outside goal posts: corner or goal kick
            defending_goal_x = 0.0 if self.possession_team.attacking_direction == 1 else 100.0
            last_touch_is_defender = (self.ball.last_touch_team_id == self.defending_team.team_id)

            if last_touch_is_defender:
                # CORNER KICK to attacking team
                corner_x = 100.0 if bx >= 100.0 else 0.0
                corner_y = 0.0 if by < 50.0 else 100.0
                setup_corner(corner_x, corner_y, self.possession_team, self.defending_team, self.ball)
                self.active_set_piece = SetPieceType.corner
                self.set_piece_timer = 0.0
            else:
                # GOAL KICK to defending team
                gk_team = self.home_team if bx <= 0.0 else self.away_team
                gk = [p for p in gk_team.players if p.role == "GK"][0]
                self.ball.x = 5.0 if bx <= 0.0 else 95.0
                self.ball.y = 50.0
                self.ball.carrier_id = gk.player_id
                self.ball.state = BallState.controlled
                self.possession_team = gk_team
                zone = get_zone_for_team(self.ball.x, self.ball.y, gk_team.attacking_direction)
                self._emit_event("goal_kick", gk_team.team_id, gk.player_id, self.ball.x, self.ball.y, zone)

    # -------------------------------------------------------------------------
    # Manual Scenario Injectors
    # -------------------------------------------------------------------------

    def inject_penalty(self, attacking_team_id: str | None = None) -> None:
        """Inject a penalty kick for the requested team."""
        team = self.home_team if (not attacking_team_id or attacking_team_id == self.home_team.team_id) else self.away_team
        opp = self.away_team if team.team_id == self.home_team.team_id else self.home_team
        self.possession_team = team

        # Foul coords inside box
        foul_x = 88.0 if team.attacking_direction == 1 else 12.0
        foul_y = 50.0
        zone = "penalty_box"

        defenders = [p for p in opp.active_players if p.role in ("CB", "CDM")]
        fouler = defenders[0] if defenders else opp.active_players[0]
        taker = setup_penalty(foul_x, foul_y, team, opp, self.ball)

        self._emit_event("foul", fouler.team_id, fouler.player_id, foul_x, foul_y, zone)
        self.active_set_piece = SetPieceType.penalty
        self.set_piece_timer = 0.0

    def inject_red_card(self, offending_team_id: str | None = None) -> None:
        """Inject a cynical foul resulting in a red card."""
        team = self.away_team if (not offending_team_id or offending_team_id == self.away_team.team_id) else self.home_team
        defenders = [p for p in team.active_players if p.role in ("CB", "CDM", "LB", "RB")]
        fouler = defenders[0] if defenders else team.active_players[0]
        fouler.is_sent_off = True

        zone = get_zone_for_team(fouler.x, fouler.y, team.attacking_direction)
        self._emit_event("foul", team.team_id, fouler.player_id, fouler.x, fouler.y, zone)
        self._emit_event("red_card", team.team_id, fouler.player_id, fouler.x, fouler.y, zone)

    def inject_free_kick(self, attacking_team_id: str | None = None) -> None:
        """Inject a direct free kick on the edge of the penalty box."""
        team = self.home_team if (not attacking_team_id or attacking_team_id == self.home_team.team_id) else self.away_team
        opp = self.away_team if team.team_id == self.home_team.team_id else self.home_team
        self.possession_team = team

        spot_x = 78.0 if team.attacking_direction == 1 else 22.0
        spot_y = 50.0
        zone = "attacking_third"

        setup_free_kick(spot_x, spot_y, team, opp, self.ball)
        self.active_set_piece = SetPieceType.free_kick
        self.set_piece_timer = 0.0
        self._emit_event("free_kick", team.team_id, self.ball.carrier_id, spot_x, spot_y, zone)

    # -------------------------------------------------------------------------
    # Canonical Event Emission
    # -------------------------------------------------------------------------

    def _emit_event(
        self,
        event_type: str,
        team_id: str,
        player_id: str | None,
        x: float | None,
        y: float | None,
        zone: str | None,
        attributes: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Construct a validated CanonicalEvent payload and dispatch it."""
        # Ensure strict clock monotonicity
        current_clock_seconds = self.minute * 60 + self.second
        if current_clock_seconds < self.last_event_clock_seconds:
            # Clamp to last seen seconds to avoid out-of-order rejection
            self.minute = self.last_event_clock_seconds // 60
            self.second = self.last_event_clock_seconds % 60
        self.last_event_clock_seconds = self.minute * 60 + self.second

        self.event_counter += 1
        clean_match_id = self.match_id.replace("-", "_")
        event_id = f"sim_{clean_match_id}_{self.event_counter}_{uuid.uuid4().hex[:6]}"

        payload: dict[str, Any] = {
            "schema_version": "event-v1",
            "event_id": event_id,
            "match_id": self.match_id,
            "minute": self.minute,
            "second": self.second,
            "event_type": event_type,
            "team_id": team_id,
            "player_id": player_id,
            "x": round(x, 2) if x is not None else None,
            "y": round(y, 2) if y is not None else None,
            "zone": zone,
            "timestamp": datetime.now(UTC).isoformat(),
            "source": {
                "adapter": "synthetic-model",
                "source_event_id": event_id,
                "raw_metadata": {
                    "synthetic": True,
                    "model": "physics_tactical_v1",
                    "home_score": self.home_team.score,
                    "away_score": self.away_team.score,
                },
            },
            "attributes": attributes or {},
        }

        self.recent_events.append(payload)
        if len(self.recent_events) > 200:
            self.recent_events.pop(0)

        if self.event_callback:
            try:
                self.event_callback(payload)
            except Exception:
                pass

        return payload

    def _event_cooldown_ok(self, event_type: str, cooldown_sec: float) -> bool:
        last = self.cooldown_events.get(event_type, -999.0)
        if (self.total_match_seconds - last) >= cooldown_sec:
            self.cooldown_events[event_type] = self.total_match_seconds
            return True
        return False

    def _get_player_by_id(self, player_id: str | None) -> Player | None:
        if not player_id:
            return None
        for p in self.all_players:
            if p.player_id == player_id:
                return p
        return None

    def get_snapshot(self) -> dict[str, Any]:
        """Return full spatial tracking snapshot of all 22 players and ball."""
        return {
            "match_id": self.match_id,
            "phase": self.phase.value,
            "minute": self.minute,
            "second": self.second,
            "clock_display": f"{self.minute}:{self.second:02d}",
            "is_paused": self.is_paused,
            "speed_multiplier": self.speed_multiplier,
            "home_team": {
                "team_id": self.home_team.team_id,
                "name": self.home_team.name,
                "short_name": self.home_team.short_name,
                "primary_color": self.home_team.primary_color,
                "secondary_color": self.home_team.secondary_color,
                "score": self.home_team.score,
                "direction": self.home_team.attacking_direction,
                "players": [p.to_dict() for p in self.home_team.players],
            },
            "away_team": {
                "team_id": self.away_team.team_id,
                "name": self.away_team.name,
                "short_name": self.away_team.short_name,
                "primary_color": self.away_team.primary_color,
                "secondary_color": self.away_team.secondary_color,
                "score": self.away_team.score,
                "direction": self.away_team.attacking_direction,
                "players": [p.to_dict() for p in self.away_team.players],
            },
            "ball": self.ball.to_dict(),
            "possession_team_id": self.possession_team.team_id,
            "active_set_piece": self.active_set_piece.value,
            "event_count": self.event_counter,
        }
