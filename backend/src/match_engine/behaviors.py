"""Per-player AI and kicks — deterministic port of frontend/match.html.

Every stochastic choice draws from the match ``SeededRng`` (no ambient randomness),
so a match is reproducible. Targets are set on player bodies; physics moves them.
"""
from __future__ import annotations
import math

from src.seed.rng import SeededRng
from .physics import FIELD_L, FIELD_W, GOAL_W, PAD, clamp, dist, seg_dist
from .tactics import STYLES, TacticalStyle
from .world import Player, TeamState, World

SHOOT_R = 19.0
TACKLE_R = 1.7
CONTROL_R = 1.25


def style_of(t: TeamState) -> TacticalStyle:
    return STYLES[t.style_key]


def formation_xy(p: Player, st: TacticalStyle) -> tuple[float, float]:
    line_shift = (st.line - 0.4) * 0.18
    role_w = 1.2 if p.role == "DEF" else 0.4 if p.role == "FWD" else 1.0
    dd = clamp(p.fx + line_shift * role_w, .03, .96)
    wy = clamp(0.5 + (p.fy - 0.5) * st.width, .05, .95)
    x = (dd if p.dir > 0 else 1 - dd) * FIELD_L
    return x, wy * FIELD_W


def offside_line_for(world: World, idx: int) -> float:
    defending = world.teams[1 - idx]
    d = world.teams[idx].dir
    xs = sorted((p.x for p in world.active(defending)), reverse=(d < 0))
    second_last = xs[1] if len(xs) > 1 else xs[0]
    half = FIELD_L / 2
    return max(second_last, half) if d > 0 else min(second_last, half)


def beyond(d: int, x: float, line: float) -> bool:
    return x > line + 0.4 if d > 0 else x < line - 0.4


def in_opp_half(t: TeamState, x: float) -> bool:
    return x > FIELD_L / 2 if t.dir > 0 else x < FIELD_L / 2


def nearest_opp(world: World, p: Player) -> float:
    d = 1e9
    for o in world.active(world.teams[1 - p.team]):
        d = min(d, dist(p.x, p.y, o.x, o.y))
    return d


def lane_clear(world: World, ax, ay, bx, by, attack_idx) -> bool:
    for o in world.active(world.teams[1 - attack_idx]):
        if seg_dist(o.x, o.y, ax, ay, bx, by) < 1.7:
            return False
    return True


def set_target(p: Player, tx: float, ty: float, mv: float) -> None:
    p.tx = clamp(tx, PAD, FIELD_L - PAD)
    p.ty = clamp(ty, PAD, FIELD_W - PAD)
    p.mv = mv


def gk_target(world: World, rng: SeededRng, p: Player, t: TeamState) -> None:
    ball = world.ball
    gx = t.own_goal_x + t.dir * 2.2
    tx, ty, mv = gx, clamp(ball.y, FIELD_W / 2 - GOAL_W, FIELD_W / 2 + GOAL_W), p.max_v
    dz = dist(ball.x, ball.y, t.own_goal_x, FIELD_W / 2)
    carrier = ball.carrier
    if dz < 17 and (carrier is None or carrier.team != t.idx):
        tx = clamp(ball.x, t.own_goal_x + t.dir * 1, t.own_goal_x + t.dir * 9)
        ty, mv = ball.y, mv * 1.15
    if carrier is p:                              # GK on the ball: clear it long
        m = best_pass_target(world, p, t, True)
        mx, my = (m.x, m.y) if m else (t.goal_x, FIELD_W / 2)
        kick(world, rng, p, t, mx, my, 30, True, None)
        return
    set_target(p, tx, ty, mv)


def best_pass_target(world: World, c: Player, t: TeamState, want_forward: bool):
    best, bs = None, -1e9
    oline = offside_line_for(world, t.idx)
    for m in world.active(t):
        if m is c or m.role == "GK":
            continue
        if beyond(t.dir, m.x, oline) and in_opp_half(t, m.x):
            continue
        dd = dist(c.x, c.y, m.x, m.y)
        fwd = (m.x - c.x) * t.dir
        s = fwd * (1.6 if want_forward else 1.0) + nearest_opp(world, m) * 1.1 - abs(dd - style_of(t).pass_len) * 0.2
        if s > bs:
            bs, best = s, m
    return best


def decide_action(world: World, rng: SeededRng, c: Player, t: TeamState, st: TacticalStyle) -> dict:
    d, goal_x, oline = t.dir, t.goal_x, offside_line_for(world, t.idx)
    dgoal = dist(c.x, c.y, goal_x, FIELD_W / 2)
    np = nearest_opp(world, c)

    def noise() -> float:
        return rng.uniform(-1.2, 1.2)

    shoot_score = -1e9
    if dgoal < SHOOT_R and abs(c.y - FIELD_W / 2) < 26:
        ang = 1 - abs(c.y - FIELD_W / 2) / 34
        shoot_score = ((SHOOT_R - dgoal) * 0.55 + ang * 9
                       + (2 if st.counter > 0.7 else 0) + (2 if np < 2.5 else 0)
                       + c.shooting * 4 + noise())

    pass_score, recv = -1e9, None
    for m in world.active(t):
        if m is c or m.role == "GK":
            continue
        if beyond(d, m.x, oline) and in_opp_half(t, m.x):
            continue
        dd = dist(c.x, c.y, m.x, m.y)
        if dd < 2.5 or dd > st.pass_len * 2.4:
            continue
        if not lane_clear(world, c.x, c.y, m.x, m.y, t.idx):
            continue
        fwd, open_ = (m.x - c.x) * d, nearest_opp(world, m)
        s = 6 + fwd * 1.05 + open_ * 1.0 - abs(dd - st.pass_len) * 0.22 + st.possess * 4 + c.passing * 2 + noise()
        if s > pass_score:
            pass_score, recv = s, m

    ahead_x = c.x + d * 7
    ahead_clear = lane_clear(world, c.x, c.y, ahead_x, c.y, t.idx)
    drib_score = (2 + (3 if np > 5 else -2 if np < 2 else 0.5) + (1 - st.possess) * 2
                  + (2.5 if ahead_clear else -3) + (1.5 if dgoal < 35 else 0)
                  + c.skill * 1.5 + noise())

    if shoot_score >= pass_score and shoot_score >= drib_score and shoot_score > -1e8:
        return {"type": "shoot"}
    if pass_score >= drib_score and recv is not None:
        return {"type": "pass", "recv": recv}
    return {"type": "dribble", "tx": goal_x, "ty": FIELD_W / 2}


def carrier_decide(world: World, rng: SeededRng, c: Player, t: TeamState, st: TacticalStyle, dt: float) -> None:
    c.dec_t -= dt
    if c.dec_t <= 0 or not c.action:
        c.dec_t = 0.18
        c.action = decide_action(world, rng, c, t, st)
    a = c.action
    if a["type"] == "shoot":
        shoot(world, rng, c, t)
        c.action = None
        return
    if a["type"] == "pass" and a.get("recv") and not a["recv"].sent_off:
        r = a["recv"]
        power = clamp(dist(c.x, c.y, r.x, r.y) * 1.15, 9, 32)
        kick(world, rng, c, t, r.x + r.dir * 1.4, r.y, power, False, r)
        c.action = None
        return
    tx, ty = a["tx"], a["ty"]
    np = nearest_opp(world, c)
    if np < 2.2:
        ty += 6 if c.y < FIELD_W / 2 else -6
    set_target(c, tx, ty, c.mv * (0.8 if np < 2.4 else 1.0))


def attacker_off_ball(world: World, p: Player, t: TeamState, st: TacticalStyle, oline: float, carrier) -> None:
    base_x, base_y = formation_xy(p, st)
    push = 14 if p.role == "FWD" else 8 if p.role == "MID" else st.overlap * 9
    tx, ty = base_x + t.dir * push, base_y
    ball = world.ball
    if carrier is not None:
        supports = sorted((q for q in world.active(t) if q is not carrier and q.role != "GK"),
                          key=lambda q: dist(q.x, q.y, carrier.x, carrier.y))[:2]
        if p in supports:
            ang = -1 if p.y < carrier.y else 1
            off = st.pass_len * 0.9
            tx = carrier.x + t.dir * off * 0.7
            ty = clamp(carrier.y + ang * off * 0.6, PAD, FIELD_W - PAD)
    if p.role in ("FWD", "MID"):
        ball_fwd = (ball.vx * t.dir > 4) and ball.carrier is None
        if beyond(t.dir, tx, oline) and not ball_fwd:
            tx = oline - 0.8 if t.dir > 0 else oline + 0.8
            p.mv *= 0.96
        elif beyond(t.dir, tx, oline) and ball_fwd:
            p.mv *= 1.12
    tx += (ball.x - tx) * 0.08
    ty += (ball.y - ty) * 0.12
    set_target(p, tx, ty, p.mv)


def defender_mark(world: World, p: Player, t: TeamState, st: TacticalStyle) -> None:
    base_x, base_y = formation_xy(p, st)
    opp, bd = None, 1e9
    for o in world.active(world.teams[1 - t.idx]):
        if o.role == "GK":
            continue
        dd = dist(p.x, p.y, o.x, o.y)
        if dd < bd:
            bd, opp = dd, o
    ball = world.ball
    if opp is not None and bd < 22:
        tx = opp.x - t.dir * 1.6
        ty = opp.y + (0.4 if opp.y < FIELD_W / 2 else -0.4)
    else:
        tx, ty = base_x - t.dir * (1 - st.line) * 6, base_y
    tx += (ball.x - tx) * 0.08 * (1 - st.compact * 0.4)
    ty += (ball.y - ty) * 0.18 * st.compact
    set_target(p, tx, ty, p.mv * 0.98)


def kick(world: World, rng: SeededRng, c: Player, t: TeamState, tx, ty, power, is_clear, recv) -> None:
    ball = world.ball
    ball.carrier = None
    ball.kick_lock = 0.30
    ball.last_kick = c
    ball.intended = recv
    c.tackle_cool = 0.25
    dx, dy = tx - ball.x, ty - ball.y
    d = math.hypot(dx, dy) or 1.0
    ball.vx = dx / d * power + rng.uniform(-1, 1)
    ball.vy = dy / d * power + rng.uniform(-1, 1)
    if recv is not None and not is_clear:        # an intentional pass (not a clearance/shot)
        c.passes_att += 1
        ball.last_passer = c
    oline = offside_line_for(world, t.idx)
    if recv and beyond(t.dir, recv.x, oline) and in_opp_half(t, recv.x) and beyond(t.dir, recv.x, ball.x):
        ball.offside_mark = {"team": t.idx, "recv": recv, "line": oline}
    else:
        ball.offside_mark = None


def shoot(world: World, rng: SeededRng, c: Player, t: TeamState) -> None:
    # Aim spread can exceed the goal mouth (3.66 m half-width) so some shots miss wide;
    # accuracy improves with the shooter's finishing.
    spread = 5.4 - c.shooting * 1.4
    gy = FIELD_W / 2 + rng.uniform(-1, 1) * spread
    kick(world, rng, c, t, t.goal_x, gy, rng.uniform(22, 29), True, None)
    world.ball.offside_mark = None
    world.shots[t.idx] += 1
    c.shots_p += 1


def ai_step(world: World, rng: SeededRng, dt: float) -> None:
    if world.state != "play":
        return
    ball = world.ball
    carrier = ball.carrier
    owner = carrier.team if carrier else -1
    pbx, pby = ball.x + ball.vx * 0.35, ball.y + ball.vy * 0.35

    for t in world.teams:
        st = style_of(t)
        oline = offside_line_for(world, t.idx)
        attacking = owner == t.idx
        ranked = sorted((p for p in world.active(t) if p.role != "GK"),
                        key=lambda p: dist(p.x, p.y, ball.x, ball.y))
        for p in world.active(t):
            if p.tackle_cool > 0:
                p.tackle_cool -= dt
            # tired legs are slower: stamina (1 fresh .. 0.25 spent) scales top speed.
            p.mv = p.max_v * st.tempo * (0.72 + 0.28 * p.stamina)
            if p.role == "GK":
                gk_target(world, rng, p, t)
                continue
            if p is carrier:
                carrier_decide(world, rng, p, t, st, dt)
                continue
            if attacking:
                attacker_off_ball(world, p, t, st, oline, carrier)
                continue
            if owner == 1 - t.idx:
                k = max(1, round(1 + st.press * 2))
                idx = ranked.index(p) if p in ranked else -1
                if 0 <= idx < k:
                    set_target(p, carrier.x if carrier else pbx, carrier.y if carrier else pby, p.mv * 1.05)
                else:
                    defender_mark(world, p, t, st)
                continue
            if ranked and p is ranked[0]:
                set_target(p, pbx, pby, p.mv * 1.08)
            else:
                bx, by = formation_xy(p, st)
                set_target(p, bx + (ball.x - bx) * 0.18, by + (ball.y - by) * 0.25, p.mv * 0.95)
