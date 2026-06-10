"""Team, coach, and tactical identity."""
from __future__ import annotations
from enum import Enum
from pydantic import BaseModel, Field
from .player import Player


class StyleDNA(str, Enum):
    POSSESSION = "possession"; HIGH_PRESS = "high_press"; COUNTER = "counter"
    DIRECT = "direct"; BALANCED = "balanced"


class Formation(str, Enum):
    F433 = "4-3-3"; F442 = "4-4-2"; F352 = "3-5-2"; F4231 = "4-2-3-1"


class CoachProfile(BaseModel):
    formation: Formation = Formation.F433
    aggression: float = Field(ge=0, le=1)
    line_height: float = Field(ge=0, le=1)
    tempo: float = Field(ge=0, le=1)
    pressing: float = Field(ge=0, le=1)
    directness: float = Field(ge=0, le=1)


class Team(BaseModel):
    id: str
    nation: str
    tier: int = Field(ge=1, le=4)
    style_dna: StyleDNA
    rating: float
    squad: list[Player]
    xi: list[str]
    coach: CoachProfile
    colors: dict[str, str] = {"primary": "#2bb673", "secondary": "#ff7a18"}
