"""One AI per team: a slow Coach plan + a fast per-frame role allocation.

The orchestrator holds a pluggable DecisionPolicy (Strategy pattern) and, given a
TeamView of the current pitch state, returns each player's target position.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from .policies.base import DecisionPolicy


@dataclass
class TeamView:
    """What a team perceives this frame (one side's point of view)."""
    side: str                       # "home" | "away"
    push: float                     # 0 = sit deep, 1 = commit forward
    ball: tuple[float, float]
    carrier: Optional[int] = None   # index of this team's player on the ball
    presser: Optional[int] = None   # index of this team's player closest to the ball


class TeamOrchestrator:
    def __init__(self, policy: DecisionPolicy) -> None:
        self._policy = policy
        self._plan: dict = {}

    def coach_plan(self, coach) -> dict:
        """Translate a coach profile into tempo/line-height knobs (slow loop)."""
        self._plan = {
            "line_height": getattr(coach, "line_height", 0.5),
            "tempo": getattr(coach, "tempo", 0.5),
            "pressing": getattr(coach, "pressing", 0.5),
        }
        return self._plan

    def orchestrate(self, view: TeamView) -> dict[int, tuple[float, float]]:
        """Per-player target positions for this frame (fast loop)."""
        return self._policy.allocate_roles(view, self._plan)
