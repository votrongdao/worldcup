"""Deterministic 2D pitch physics: arrive-steering, separation, ball, goal detection.

Pure functions over the World. Pitch is 105 x 68 m; home (dir +1) attacks toward
x=105, away (dir -1) toward x=0. Goal mouth spans 7.32 m centred on y=34.
"""
from __future__ import annotations
import math

from .world import World

FIELD_L = 105.0
FIELD_W = 68.0
GOAL_W = 7.32
BOX_D = 16.5
BOX_W = 40.3
PEN_SPOT = 11.0
PAD = 1.5
GOAL_Y0 = FIELD_W / 2 - GOAL_W / 2
GOAL_Y1 = FIELD_W / 2 + GOAL_W / 2


def clamp(v: float, lo: float, hi: float) -> float:
    return lo if v < lo else hi if v > hi else v


def dist(ax: float, ay: float, bx: float, by: float) -> float:
    return math.hypot(ax - bx, ay - by)


def seg_dist(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> float:
    """Distance from point P to segment AB (for pass-lane / interception checks)."""
    dx, dy = bx - ax, by - ay
    l2 = dx * dx + dy * dy or 1e-6
    t = clamp(((px - ax) * dx + (py - ay) * dy) / l2, 0.0, 1.0)
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def step_players(world: World, dt: float) -> None:
    bodies = [p for t in world.teams for p in world.active(t)]
    # Arrive-steering: accelerate toward target, cap speed, integrate.
    for p in bodies:
        dx, dy = p.tx - p.x, p.ty - p.y
        d = math.hypot(dx, dy) or 1e-6
        desired = min(p.mv, d * 3.2)
        dvx, dvy = dx / d * desired - p.vx, dy / d * desired - p.vy
        dl = math.hypot(dvx, dvy) or 1e-6
        a = min(p.accel * dt, dl)
        p.vx += dvx / dl * a
        p.vy += dvy / dl * a
        sp = math.hypot(p.vx, p.vy)
        if sp > p.mv:
            p.vx, p.vy = p.vx / sp * p.mv, p.vy / sp * p.mv
        p.x += p.vx * dt
        p.y += p.vy * dt
        p.x, p.y = clamp(p.x, PAD, FIELD_L - PAD), clamp(p.y, PAD, FIELD_W - PAD)
    # Player–player separation (positional, no velocity kill).
    n = len(bodies)
    for i in range(n):
        a = bodies[i]
        for j in range(i + 1, n):
            b = bodies[j]
            dx, dy = b.x - a.x, b.y - a.y
            d = math.hypot(dx, dy)
            mn = a.r + b.r
            if 1e-4 < d < mn:
                ov, nx, ny = (mn - d) / 2, dx / d, dy / d
                a.x -= nx * ov; a.y -= ny * ov
                b.x += nx * ov; b.y += ny * ov


def in_goal_y(y: float) -> bool:
    return GOAL_Y0 <= y <= GOAL_Y1


def step_ball(world: World, dt: float) -> str | None:
    """Advance the ball. Returns "goal_home"/"goal_away"/"out_left"/"out_right"/"out_y"
    or None. A dribbling carrier keeps the ball just ahead of them."""
    ball = world.ball
    if world.state != "play":
        return None
    if ball.kick_lock > 0:
        ball.kick_lock -= dt

    if ball.carrier is not None:
        c = ball.carrier
        hx, hy = c.vx, c.vy
        hs = math.hypot(hx, hy)
        if hs < 0.6:
            hx, hy = float(c.dir), 0.0
        else:
            hx, hy = hx / hs, hy / hs
        cpx, cpy = c.x + hx * 1.0, c.y + hy * 1.0
        ball.vx = (cpx - ball.x) / dt * 0.45
        ball.vy = (cpy - ball.y) / dt * 0.45
        ball.x += ball.vx * dt
        ball.y += ball.vy * dt
        return None

    ball.x += ball.vx * dt
    ball.y += ball.vy * dt
    damp = 0.62 ** dt
    ball.vx *= damp
    ball.vy *= damp
    if ball.y < PAD:
        ball.y, ball.vy = PAD, -ball.vy * 0.55
    elif ball.y > FIELD_W - PAD:
        ball.y, ball.vy = FIELD_W - PAD, -ball.vy * 0.55

    # Goalkeeper shot-stop: a fast ball near a goal that the defending GK can reach is
    # saved (controlled). Reach scales with GK quality. This keeps conversion realistic
    # despite the coarse timestep (a 30 m/s shot would otherwise blow past the keeper).
    speed = math.hypot(ball.vx, ball.vy)
    if speed > 5:
        defend = None
        if ball.vx < 0 and ball.x < 22:
            defend = world.teams[0]
        elif ball.vx > 0 and ball.x > FIELD_L - 22:
            defend = world.teams[1]
        if defend is not None:
            gk = next((p for p in world.active(defend) if p.role == "GK"), None)
            if gk is not None:
                reach = 4.3 + gk.skill * 2.6 + gk.r
                if math.hypot(gk.x - ball.x, gk.y - ball.y) < reach:
                    ball.carrier = gk
                    ball.vx *= 0.12
                    ball.vy *= 0.12
                    ball.last_kick = gk
                    return "save"

    if ball.x <= 0.4:
        return "goal_away" if in_goal_y(ball.y) else "out_left"
    if ball.x >= FIELD_L - 0.4:
        return "goal_home" if in_goal_y(ball.y) else "out_right"
    return None
