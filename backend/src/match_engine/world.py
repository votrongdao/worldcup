"""Mutable per-match world state: player bodies, ball, score, clock. Lives only
during a single match (discarded after, except the recorded event/frame log)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Player:
    """A runtime player body. Physical stats are derived from the generated Player."""
    team: int                 # 0 = home, 1 = away
    dir: int                  # +1 attacks toward x=105, -1 toward x=0
    role: str                 # GK/DEF/MID/FWD
    fx: float                 # formation x-fraction
    fy: float                 # formation y-fraction
    pid: str                  # generated player id
    max_v: float
    accel: float
    skill: float              # technical quality (0..1)
    aggr: float               # foul tendency (0..1)
    shooting: float
    passing: float
    x: float = 0.0
    y: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    r: float = 0.95
    tx: float = 0.0           # target x
    ty: float = 0.0           # target y
    mv: float = 7.0           # this-frame max speed
    tackle_cool: float = 0.0
    dec_t: float = 0.0        # time until next carrier decision
    action: Optional[dict] = None
    yellow: int = 0
    sent_off: bool = False


@dataclass
class Ball:
    x: float = 52.5
    y: float = 34.0
    vx: float = 0.0
    vy: float = 0.0
    r: float = 0.55
    carrier: Optional[Player] = None
    kick_lock: float = 0.0
    last_kick: Optional[Player] = None
    intended: Optional[Player] = None
    offside_mark: Optional[dict] = None


@dataclass
class TeamState:
    idx: int
    dir: int
    form_key: str
    style_key: str
    players: list[Player]
    coach_t: float
    goal_x: float
    own_goal_x: float


@dataclass
class World:
    teams: list[TeamState]
    ball: Ball
    score: list[int] = field(default_factory=lambda: [0, 0])
    shots: list[int] = field(default_factory=lambda: [0, 0])
    poss: list[int] = field(default_factory=lambda: [0, 0])   # frames each team had the ball
    clock: float = 0.0
    half: int = 1
    state: str = "kickoff"        # kickoff | play | dead
    state_t: float = 0.0
    dead_ball: Optional[dict] = None
    last_touch_team: int = 0

    def active(self, t: TeamState) -> list[Player]:
        return [p for p in t.players if not p.sent_off]
