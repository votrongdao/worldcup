"""API request/response DTOs (camelCase on the wire, kept separate from domain)."""
from __future__ import annotations
from typing import Optional

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from src.domain.tournament import Phase, TournamentConfig


class CamelModel(BaseModel):
    """Serialise to camelCase; still accept snake_case on input."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class CreateTournamentRequest(BaseModel):
    # Input may arrive as camelCase (frontend) or snake_case (curl/tests).
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    config: TournamentConfig


class CreateTournamentResponse(CamelModel):
    id: str


class TournamentStatus(CamelModel):
    id: str
    phase: Phase
    run_hash: str = ""
    champion_id: Optional[str] = None
    teams: int = 0
    groups: int = 0


class StandingDTO(CamelModel):
    team_id: str
    group: str = ""
    played: int = 0
    w: int = 0
    d: int = 0
    l: int = 0
    gf: int = 0
    ga: int = 0
    pts: int = 0


class TeamSummaryDTO(CamelModel):
    id: str
    nation: str
    tier: int
    rating: float
    style_dna: str
    group: str = ""


class MatchSummaryDTO(CamelModel):
    match_id: str
    home_id: str
    away_id: str
    phase: Phase
    score_home: int
    score_away: int
    decided_by: str
    winner_id: Optional[str] = None


class BracketSlotDTO(CamelModel):
    match_id: str
    phase: Phase
    home_id: Optional[str] = None
    away_id: Optional[str] = None
    winner_id: Optional[str] = None


class PlayerDTO(CamelModel):
    id: str
    role: str
    pace: float
    accel: float
    shooting: float
    passing: float
    dribbling: float
    vision: float
    defending: float
    stamina: float
    teamwork: float


class CoachDTO(CamelModel):
    formation: str
    aggression: float
    line_height: float
    tempo: float
    pressing: float
    directness: float


class TeamDetailDTO(CamelModel):
    id: str
    nation: str
    tier: int
    rating: float
    style_dna: str
    group: str = ""
    xi: list[str]
    squad: list[PlayerDTO]
    coach: CoachDTO
    colors: dict[str, str] = {}


class AiTextDTO(CamelModel):
    text: str
    cached: bool = False

