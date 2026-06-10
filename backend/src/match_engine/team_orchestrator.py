"""One AI per team: slow Coach loop + fast Role-Allocator loop behind a DecisionPolicy."""
from __future__ import annotations
from .policies.base import DecisionPolicy


class TeamOrchestrator:
    def __init__(self, policy: DecisionPolicy) -> None:
        self._policy = policy
        self._plan = None

    def coach_plan(self, state, due: bool):
        if due:
            self._plan = ...  # TODO: formation, line height, tempo, aggression, press.
        return self._plan

    def orchestrate(self, state) -> dict:
        roles = self._policy.allocate_roles(state, self._plan)
        return roles  # TODO: -> per-player commands via behaviors + resolve_action.
