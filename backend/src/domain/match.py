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


class MatchResult(BaseModel):
    match_id: str
    score_home: int
    score_away: int
    decided_by: Literal["regulation", "extra_time", "penalties"]
    winner: Optional[Literal["home", "away"]]
    events: list[MatchEvent] = []
    stats: MatchStats = MatchStats()
    frames: list[dict] = []          # populated only when frame capture is requested


class Action(BaseModel):
    kind: Literal["move", "pass", "shoot", "dribble", "clear", "hold"]
    target: tuple[float, float] | None = None
