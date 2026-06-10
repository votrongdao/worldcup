"""Deterministic 2D pitch physics: steering, integration, bounds, goal detection.

Pure helpers (no I/O, no global state) used by the replay choreographer and the
team policies. The pitch is 105 x 68 metres; home attacks toward x = 105, away
toward x = 0. Goal mouth spans y in [30.34, 37.66] (a 7.32 m goal).
"""
from __future__ import annotations
import math
from dataclasses import dataclass

FIELD_L = 105.0
FIELD_W = 68.0
GOAL_Y0 = 30.34
GOAL_Y1 = 37.66


@dataclass
class Body:
    """A moving point (player or ball) with position and velocity."""
    x: float
    y: float
    vx: float = 0.0
    vy: float = 0.0


def clamp(v: float, lo: float, hi: float) -> float:
    return lo if v < lo else hi if v > hi else v


def clamp_to_field(x: float, y: float, margin: float = 0.0) -> tuple[float, float]:
    return clamp(x, -margin, FIELD_L + margin), clamp(y, 0.0, FIELD_W)


def dist(ax: float, ay: float, bx: float, by: float) -> float:
    return math.hypot(ax - bx, ay - by)


def steer(body: Body, tx: float, ty: float, max_speed: float, accel: float,
          dt: float) -> None:
    """Accelerate a body toward (tx, ty) up to max_speed, then integrate one step.

    Velocity is nudged toward the desired heading (acceleration limit), capped at
    max_speed, and position advanced by dt. Mutates ``body`` in place.
    """
    dx, dy = tx - body.x, ty - body.y
    d = math.hypot(dx, dy)
    if d < 1e-6:
        desired_vx = desired_vy = 0.0
    else:
        speed = min(max_speed, d / dt)        # ease in as the target nears
        desired_vx = dx / d * speed
        desired_vy = dy / d * speed
    body.vx += clamp(desired_vx - body.vx, -accel * dt, accel * dt)
    body.vy += clamp(desired_vy - body.vy, -accel * dt, accel * dt)
    body.x += body.vx * dt
    body.y += body.vy * dt
    body.x, body.y = clamp_to_field(body.x, body.y, margin=1.5)


def roll_ball(ball: Body, dt: float, friction: float = 0.94) -> None:
    """Advance a free ball with rolling friction (mutates in place)."""
    ball.x += ball.vx * dt
    ball.y += ball.vy * dt
    ball.vx *= friction
    ball.vy *= friction
    ball.x, ball.y = clamp_to_field(ball.x, ball.y)


def kick(ball: Body, tx: float, ty: float, power: float) -> None:
    """Set the ball's velocity toward a target at the given power (m/s)."""
    dx, dy = tx - ball.x, ty - ball.y
    d = math.hypot(dx, dy) or 1.0
    ball.vx = dx / d * power
    ball.vy = dy / d * power


def in_goal_mouth(y: float) -> bool:
    return GOAL_Y0 <= y <= GOAL_Y1


def attack_goal(side: str) -> tuple[float, float]:
    """The goal a side is shooting at."""
    return (FIELD_L, FIELD_W / 2) if side == "home" else (0.0, FIELD_W / 2)
