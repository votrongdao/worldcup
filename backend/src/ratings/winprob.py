"""Per-minute win-probability / risk model (logistic over rating + match state)."""
from __future__ import annotations
import math


def win_prob(rating_a: float, rating_b: float, goal_diff: int, minute: int) -> float:
    x = 0.012 * (rating_a - rating_b) + 0.5 * goal_diff
    return 1.0 / (1.0 + math.exp(-x))
