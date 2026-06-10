"""Tournament aggregate, configuration, fixtures, standings."""
from __future__ import annotations
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel
from .team import Team


class Phase(str, Enum):
    SETUP = "setup"; GENERATING = "generating"; DRAW = "draw"; GROUP = "group"
    R16 = "r16"; QF = "qf"; SF = "sf"; THIRD_PLACE = "third_place"
    FINAL = "final"; DONE = "done"


class TournamentConfig(BaseModel):
    # Accept both camelCase (frontend: perGroup) and snake_case (curl/tests).
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    format: str = "world_cup_32"
    teams: int = 32
    groups: int = 8
    per_group: int = 4
    advance_per_group: int = 2
    third_place: bool = True
    seed: int = 0


class Fixture(BaseModel):
    id: str
    phase: Phase
    home_id: str
    away_id: str
    group: Optional[str] = None       # group letter for group-stage fixtures
    matchday: int = 0                 # 1-based ordering within a round


class MatchSummary(BaseModel):
    """Compact, persisted outcome of a single fixture (full events live in the log)."""
    match_id: str
    home_id: str
    away_id: str
    phase: Phase
    score_home: int
    score_away: int
    decided_by: str = "regulation"
    winner_id: Optional[str] = None   # resolved team id (None only for legal draws)
    fairplay_home: int = 0
    fairplay_away: int = 0


class Standing(BaseModel):
    team_id: str
    group: str = ""
    played: int = 0
    w: int = 0
    d: int = 0
    l: int = 0
    gf: int = 0
    ga: int = 0
    pts: int = 0
    fair: int = 0                     # cumulative fair-play demerits (fewer is better)


class BracketSlot(BaseModel):
    match_id: str
    phase: Phase
    home_id: Optional[str] = None
    away_id: Optional[str] = None
    winner_id: Optional[str] = None


class Tournament(BaseModel):
    id: str
    config: TournamentConfig
    phase: Phase = Phase.SETUP
    run_hash: str = ""
    group_of: dict[str, str] = {}                       # team_id -> group letter
    teams: dict[str, Team] = {}                         # team_id -> generated team
    fixtures: list[Fixture] = []
    results: dict[str, MatchSummary] = {}               # match_id -> summary
    standings: dict[str, list[Standing]] = {}           # group letter -> ordered table
    bracket: list[BracketSlot] = []
    champion_id: Optional[str] = None
    runner_up_id: Optional[str] = None
    third_place_id: Optional[str] = None
