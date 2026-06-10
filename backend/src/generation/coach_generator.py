"""Generate a coach profile aligned to the nation's style DNA."""
from __future__ import annotations
from src.domain.team import CoachProfile, Formation, StyleDNA
from src.seed.rng import SeededRng


def generate_coach(nation_seed: int, dna: StyleDNA) -> CoachProfile:
    rng = SeededRng(nation_seed ^ 0x9E3779B9)
    press = 0.8 if dna in (StyleDNA.HIGH_PRESS,) else rng.uniform(0.4, 0.7)
    return CoachProfile(
        formation=Formation.F433,
        aggression=rng.uniform(0.4, 0.8), line_height=rng.uniform(0.4, 0.7),
        tempo=rng.uniform(0.4, 0.85), pressing=press, directness=rng.uniform(0.3, 0.7),
    )
