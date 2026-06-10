"""Player domain model. Pure, no I/O."""
from __future__ import annotations
from enum import Enum
from pydantic import BaseModel, Field


class Role(str, Enum):
    GK = "GK"; DEF = "DEF"; MID = "MID"; FWD = "FWD"


class Player(BaseModel):
    id: str
    role: Role
    pace: float = Field(ge=0, le=1)
    accel: float = Field(ge=0, le=1)
    shooting: float = Field(ge=0, le=1)
    passing: float = Field(ge=0, le=1)
    dribbling: float = Field(ge=0, le=1)
    vision: float = Field(ge=0, le=1)
    defending: float = Field(ge=0, le=1)
    stamina: float = Field(ge=0, le=1)
    teamwork: float = Field(ge=0, le=1)
    mass: float = 1.0
