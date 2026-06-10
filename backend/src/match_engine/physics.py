"""Deterministic physics: kinematics, momentum collisions, ball + goal dynamics."""
from __future__ import annotations
from .world import MatchWorldState


class PhysicsEngine:
    def integrate(self, world: MatchWorldState, dt: float) -> None:
        ...  # TODO: integrate velocities, friction, accel limits.

    def resolve_collisions(self, world: MatchWorldState) -> None:
        ...  # TODO: circle-circle impulse, walls, posts, goal detection.
