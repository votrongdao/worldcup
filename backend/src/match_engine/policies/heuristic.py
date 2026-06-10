"""Default deterministic utility/heuristic policy (consolidation of think()/decide())."""
from __future__ import annotations
from src.domain.match import Action
from .base import DecisionPolicy


class HeuristicPolicy(DecisionPolicy):
    def allocate_roles(self, state, plan) -> dict:
        # TODO: owner/support/runners/pressers/cover/block assignment (O(11)).
        return {}

    def resolve_action(self, player_id: str, state) -> Action:
        # TODO: clearance > shoot(box) > through-ball > pass > dribble priority.
        return Action(kind="hold")
