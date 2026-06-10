"""Pluggable RL policy (stub). Swappable for HeuristicPolicy without core changes."""
from __future__ import annotations
from src.domain.match import Action
from .base import DecisionPolicy


class RLPolicy(DecisionPolicy):
    def __init__(self, weights_path: str | None = None) -> None:
        self._weights_path = weights_path  # TODO: load a trained policy network.

    def allocate_roles(self, state, plan) -> dict: return {}
    def resolve_action(self, player_id: str, state) -> Action: return Action(kind="hold")
