"""Behaviour resolver: formation shape + per-player target positions.

Positions are given for a team attacking toward +x (home). Away teams mirror on x.
Each slot is (x_fraction, y_fraction) of the pitch in the team's DEFENSIVE shape;
a per-frame "push" shifts the whole block up the pitch when the team has the ball.
"""
from __future__ import annotations
from .physics import FIELD_L, FIELD_W

# 4-3-3 in [GK, 4x DEF, 3x MID, 3x FWD] order (matches the generated XI ordering).
FORMATION_433: list[tuple[float, float]] = [
    (0.05, 0.50),                                            # GK
    (0.20, 0.18), (0.20, 0.39), (0.20, 0.61), (0.20, 0.82),  # DEF
    (0.40, 0.28), (0.43, 0.50), (0.40, 0.72),               # MID
    (0.66, 0.25), (0.70, 0.50), (0.66, 0.75),               # FWD
]

_ATTACK_SHIFT = 0.26   # how far up the pitch the block slides when attacking


def base_slot(index: int, side: str) -> tuple[float, float]:
    """Resting position for player ``index`` of ``side`` (metres)."""
    fx, fy = FORMATION_433[index]
    x = fx * FIELD_L
    if side == "away":
        x = FIELD_L - x
    return x, fy * FIELD_W


def target_for(index: int, side: str, push: float) -> tuple[float, float]:
    """Formation slot shifted up-pitch by ``push`` in [0,1] (1 = full attack)."""
    x, y = base_slot(index, side)
    shift = _ATTACK_SHIFT * FIELD_L * push
    x = x + shift if side == "home" else x - shift
    # The keeper barely advances.
    if index == 0:
        x = base_slot(index, side)[0] + (shift * 0.15 if side == "home" else -shift * 0.15)
    return x, y
