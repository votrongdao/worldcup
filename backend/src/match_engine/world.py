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
    # full skill profile (carried from the generated player for ratings + sub logic)
    pace: float = 0.5
    dribbling: float = 0.5
    vision: float = 0.5
    defending: float = 0.5
    stamina_attr: float = 0.5
    teamwork: float = 0.5
    overall: float = 0.5      # mean technical+physical quality, for sub ranking
    shirt: int = 0            # display number (XI/bench order)
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
    # live condition + per-match performance counters
    stamina: float = 1.0      # 1 = fresh, depletes with distance; scales speed
    min_on: float = 0.0       # clock minute this player came onto the pitch
    min_off: Optional[float] = None  # clock minute removed (sub off), else None
    distance: float = 0.0     # metres covered
    passes_att: int = 0
    passes_cmp: int = 0
    shots_p: int = 0
    goals_p: int = 0
    assists_p: int = 0
    tackles_won: int = 0
    fouls_p: int = 0
    saves_p: int = 0
    played: bool = True       # appeared in the match (starters True; bench set on entry)


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
    last_passer: Optional[Player] = None   # most recent intentional pass origin (for assists)


@dataclass
class TeamState:
    idx: int
    dir: int
    form_key: str
    style_key: str
    players: list[Player]            # always exactly 11 on-pitch bodies (subs swap in-place)
    coach_t: float
    goal_x: float
    own_goal_x: float
    name: str = ""
    bench: list[Player] = field(default_factory=list)   # not rendered until subbed on
    roster: list[Player] = field(default_factory=list)  # every body created (for ratings)
    subs_left: int = 5
    form_changes: int = 0
    style_changes: int = 0


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
