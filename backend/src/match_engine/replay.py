"""Deterministic tactical replay → pitch frames consistent with the scoreline.

Given the two teams, the match seed, and the recorded goal timeline (extracted from
the event log), this produces a list of frames (22 player positions + ball) that a
top-down canvas can animate. Ball "flow" is choreographed so goals land at exactly
the recorded minutes for the recorded side; players move via the heuristic policy
and the physics steering, so the motion is emergent and smooth, not scripted dots.
"""
from __future__ import annotations
from dataclasses import dataclass

from src.domain.team import Team
from src.seed.rng import SeededRng
from .behaviors import base_slot
from .physics import FIELD_L, FIELD_W, Body, steer
from .policies.heuristic import HeuristicPolicy
from .team_orchestrator import TeamOrchestrator, TeamView

FRAMES_PER_MIN = 4
SUBSTEPS = 6


@dataclass
class _Squad:
    side: str
    bodies: list[Body]
    speed: list[float]
    orch: TeamOrchestrator


def _make_squad(team: Team, side: str) -> _Squad:
    ids = set(team.xi)
    xi = [p for p in team.squad if p.id in ids] or team.squad[:11]
    bodies, speed = [], []
    for i in range(11):
        x, y = base_slot(i, side)
        bodies.append(Body(x, y))
        pace = xi[i].pace if i < len(xi) else 0.6
        speed.append(5.5 + 4.0 * pace)            # 5.5–9.5 m/s by pace
    orch = TeamOrchestrator(HeuristicPolicy())
    orch.coach_plan(team.coach)
    return _Squad(side, bodies, speed, orch)


def _nearest(bodies: list[Body], x: float, y: float) -> int:
    best, bd = 0, 1e18
    for i, b in enumerate(bodies):
        d = (b.x - x) ** 2 + (b.y - y) ** 2
        if d < bd:
            best, bd = i, d
    return best


def _reset(squad: _Squad) -> None:
    for i, b in enumerate(squad.bodies):
        b.x, b.y = base_slot(i, squad.side)
        b.vx = b.vy = 0.0


def _move(squad: _Squad, targets: dict[int, tuple[float, float]], dt: float) -> None:
    for i, b in enumerate(squad.bodies):
        tx, ty = targets.get(i, (b.x, b.y))
        steer(b, tx, ty, max_speed=squad.speed[i], accel=14.0, dt=dt)


def _team_push(side: str, owner: str, flow: float) -> float:
    adv = flow if side == "home" else -flow      # progress toward this side's goal
    adv = max(0.0, min(1.0, adv))
    return (0.35 + 0.65 * adv) if side == owner else (0.12 + 0.28 * adv)


def _frame(minute: float, home: _Squad, away: _Squad, ball: Body) -> dict:
    players = [[round(b.x, 2), round(b.y, 2)] for b in home.bodies] + \
              [[round(b.x, 2), round(b.y, 2)] for b in away.bodies]
    return {"t": round(minute, 2), "players": players,
            "ball": [round(ball.x, 2), round(ball.y, 2)]}


def generate_frames(home: Team, away: Team, seed: int,
                    goals: list[tuple[float, str]], duration: float) -> list[dict]:
    rng = SeededRng(seed)
    H, A = _make_squad(home, "home"), _make_squad(away, "away")
    ball = Body(FIELD_L / 2, FIELD_W / 2)
    goals = sorted(goals, key=lambda g: g[0])
    gi = 0

    owner = "home" if rng.random() < 0.5 else "away"
    flow = 0.0                       # -1 = away's goal (x=0), +1 = home's goal (x=105)
    swing = 4
    frames: list[dict] = []
    n = max(2, int(duration * FRAMES_PER_MIN))

    for f in range(n + 1):
        minute = duration * f / n

        approaching = gi < len(goals) and (goals[gi][0] - minute) <= 1.2
        if approaching:
            owner = goals[gi][1]
            flow_target = 1.0 if owner == "home" else -1.0
        else:
            swing -= 1
            if swing <= 0:
                if rng.random() < 0.35:
                    owner = "away" if owner == "home" else "home"
                swing = 3 + int(rng.random() * 5)
            # drift toward owner's attacking goal, with lateral wandering
            dir_ = 1.0 if owner == "home" else -1.0
            flow_target = max(-0.85, min(0.85, flow + dir_ * (0.25 + 0.4 * rng.random())))

        for _ in range(SUBSTEPS):
            flow += (flow_target - flow) * 0.18
            ball.x = (flow + 1.0) / 2.0 * FIELD_L
            gy = FIELD_W / 2
            ball.y += ((gy + (rng.random() - 0.5) * FIELD_W * 0.45) - ball.y) * 0.12
            ci = _nearest((H if owner == "home" else A).bodies, ball.x, ball.y)
            pi = _nearest((A if owner == "home" else H).bodies, ball.x, ball.y)
            own, opp = (H, A) if owner == "home" else (A, H)
            own_t = own.orch.orchestrate(TeamView(own.side, _team_push(own.side, owner, flow),
                                                  (ball.x, ball.y), carrier=ci))
            opp_t = opp.orch.orchestrate(TeamView(opp.side, _team_push(opp.side, owner, flow),
                                                  (ball.x, ball.y), presser=pi))
            _move(own, own_t, 1.0)
            _move(opp, opp_t, 1.0)

        if approaching and abs(flow) > 0.93:
            gi += 1
            ball = Body(FIELD_L / 2, FIELD_W / 2)
            flow = 0.0
            owner = "away" if owner == "home" else "home"
            swing = 4
            _reset(H)
            _reset(A)

        frames.append(_frame(minute, H, A, ball))

    return frames
