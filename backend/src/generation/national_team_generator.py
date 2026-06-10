"""Orchestrates per-nation generation: identity -> squad + coach -> validated team."""
from __future__ import annotations
from src.domain.team import Team
from src.seed.provider import sub_seed
from .identity import assign_identity
from .player_generator import generate_squad
from .coach_generator import generate_coach
from .team_builder import build_team


class NationalTeamGenerator:
    name = "national_team_generator"

    def generate(self, master_seed: int, index: int, nation: str) -> Team:
        ns = sub_seed(master_seed, "nation", index)
        tier, dna = assign_identity(ns)
        squad = generate_squad(ns, tier, dna)
        coach = generate_coach(ns, dna)
        return build_team(f"team-{index}", nation, tier, dna, squad, coach)
