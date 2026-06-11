"""Match request/result/event contracts (the Match Engine boundary)."""
from __future__ import annotations
from enum import Enum
from typing import Any, Literal, Optional
from pydantic import BaseModel
from .team import Team


class MatchRules(BaseModel):
    duration: float = 90.0
    extra_time: bool = False
    penalties: bool = False


class MatchRequest(BaseModel):
    match_id: str
    home: Team
    away: Team
    seed: int
    rules: MatchRules = MatchRules()
    render: bool = False


class MatchEventType(str, Enum):
    KICKOFF = "kickoff"; GOAL = "goal"; SHOT = "shot"; SAVE = "save"; OUT = "out"
    FULLTIME = "fulltime"; ET_START = "et_start"; PENALTY = "penalty"; END = "end"
    # Coach AI decisions taken during the match, plus the end-of-match report.
    SUBSTITUTION = "substitution"; FORMATION_CHANGE = "formation_change"
    TACTIC_CHANGE = "tactic_change"; REPORT = "report"


class MatchEvent(BaseModel):
    t: float
    type: MatchEventType
    team: Optional[Literal["home", "away"]] = None
    meta: dict[str, Any] = {}


class MatchStats(BaseModel):
    poss_home: float = 0.5
    shots_home: int = 0
    shots_away: int = 0
    fairplay_home: int = 0       # disciplinary demerits (yellow=1, send-off=+3)
    fairplay_away: int = 0


Side = Literal["home", "away"]


class PlayerRating(BaseModel):
    """Per-player match performance (Sofascore-style 4.0–10.0 rating) plus the
    skill-and-form strengths/weaknesses the coach reads."""
    player_id: str
    side: Side
    role: str
    shirt: int                       # display number (XI order)
    rating: float
    minutes: int
    goals: int = 0
    assists: int = 0
    shots: int = 0
    passes: int = 0
    pass_pct: float = 0.0
    tackles: int = 0
    saves: int = 0
    fouls: int = 0
    distance_km: float = 0.0
    stamina_end: float = 1.0
    sub_on: Optional[int] = None     # minute brought on (None = started)
    sub_off: Optional[int] = None    # minute taken off (None = finished)
    strengths: list[str] = []
    weaknesses: list[str] = []


class CoachDecision(BaseModel):
    """A tactical decision the AI coach made in-match."""
    t: float
    side: Side
    kind: Literal["formation", "substitution", "tactic"]
    summary: str
    reason: str


class TeamMatchReport(BaseModel):
    side: Side
    formation_end: str
    style_end: str
    strengths: list[str] = []
    weaknesses: list[str] = []
    key_player: Optional[str] = None
    key_player_rating: float = 0.0


class MatchResult(BaseModel):
    match_id: str
    score_home: int
    score_away: int
    decided_by: Literal["regulation", "extra_time", "penalties"]
    winner: Optional[Literal["home", "away"]]
    events: list[MatchEvent] = []
    stats: MatchStats = MatchStats()
    frames: list[dict] = []          # populated only when frame capture is requested
    player_ratings: list[PlayerRating] = []
    coach_decisions: list[CoachDecision] = []
    reports: list[TeamMatchReport] = []


class Action(BaseModel):
    kind: Literal["move", "pass", "shoot", "dribble", "clear", "hold"]
    target: tuple[float, float] | None = None
