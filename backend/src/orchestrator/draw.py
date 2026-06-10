"""DrawAgent: seed pots and draw groups with constraints (deterministic)."""
from __future__ import annotations
from src.domain.team import Team
from src.seed.provider import sub_seed
from src.seed.rng import SeededRng


class DrawAgent:
    name = "draw_agent"

    def draw(self, master_seed: int, teams: list[Team], groups: int) -> dict[str, str]:
        rng = SeededRng(sub_seed(master_seed, "draw"))
        order = sorted(teams, key=lambda t: (t.tier, rng.random()))
        return {t.id: chr(ord("A") + (i % groups)) for i, t in enumerate(order)}
