"""Default deterministic heuristic policy: formation shape + ball-reactive roles."""
from __future__ import annotations
from src.domain.match import Action
from ..behaviors import target_for
from ..physics import FIELD_L, FIELD_W, attack_goal
from .base import DecisionPolicy


class HeuristicPolicy(DecisionPolicy):
    def allocate_roles(self, state, plan) -> dict:
        """Return {player_index: (target_x, target_y)} for the team this frame.

        Everyone holds their formation slot (shifted up-pitch by ``push``), except:
        the carrier drives the ball toward the opponent goal, and the closest
        defender presses the ball.
        """
        push = state.push * (0.7 + 0.6 * plan.get("line_height", 0.5)) if plan else state.push
        push = max(0.0, min(1.0, push))
        targets: dict[int, tuple[float, float]] = {
            i: target_for(i, state.side, push) for i in range(11)
        }

        bx, by = state.ball
        if state.carrier is not None:
            gx, gy = attack_goal(state.side)
            # Carry the ball goal-ward: aim a few metres ahead of it toward goal.
            ahead_x = bx + (gx - bx) * 0.18
            ahead_y = by + (gy - by) * 0.18
            targets[state.carrier] = (
                max(2.0, min(FIELD_L - 2.0, ahead_x)),
                max(2.0, min(FIELD_W - 2.0, ahead_y)),
            )
        elif state.presser is not None:
            targets[state.presser] = (bx, by)
        return targets

    def resolve_action(self, player_id: str, state) -> Action:
        # Reserved for an action-level API; the replay drives movement via targets.
        return Action(kind="hold")
