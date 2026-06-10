"""Assign a tier and footballing style DNA to a nation (deterministic)."""
from __future__ import annotations
from src.domain.team import StyleDNA
from src.seed.rng import SeededRng

_STYLES = list(StyleDNA)


def assign_identity(nation_seed: int) -> tuple[int, StyleDNA]:
    rng = SeededRng(nation_seed)
    tier = rng.randint(1, 4)
    dna = _STYLES[rng.randint(0, len(_STYLES) - 1)]
    return tier, dna
