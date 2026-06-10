"""Mutable per-match world state (players, ball, score). Lives only during a match."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Ball:
    x: float = 52.5; y: float = 34.0; vx: float = 0.0; vy: float = 0.0


@dataclass
class MatchWorldState:
    players: list = field(default_factory=list)   # runtime player bodies
    ball: Ball = field(default_factory=Ball)
    score: tuple[int, int] = (0, 0)
    sim_time: float = 0.0
