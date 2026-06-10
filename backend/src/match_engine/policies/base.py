"""DecisionPolicy: the pluggable brain for a Team Orchestrator (Strategy pattern)."""
from __future__ import annotations
from typing import Protocol
from src.domain.match import Action


class DecisionPolicy(Protocol):
    def allocate_roles(self, state: "object", plan: "object") -> dict: ...
    def resolve_action(self, player_id: str, state: "object") -> Action: ...
