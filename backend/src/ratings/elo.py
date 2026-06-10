"""Elo rating update with stage-dependent K-factor."""
from __future__ import annotations
import math


def expected(ra: float, rb: float) -> float:
    return 1.0 / (1.0 + 10 ** ((rb - ra) / 400.0))


def update(ra: float, rb: float, score_a: float, knockout: bool = False) -> float:
    k = 30 if knockout else 20
    return ra + k * (score_a - expected(ra, rb))
