"""Generate a squad with position-weighted attributes scaled by tier and style DNA."""
from __future__ import annotations
from src.domain.player import Player, Role
from src.domain.team import StyleDNA
from src.seed.provider import sub_seed
from src.seed.rng import SeededRng


# Outfield layout for a 23-man squad: 3 GK, 7 DEF, 7 MID, 6 FWD (sums to 23).
_ROLES: list[Role] = (
    [Role.GK] * 3 + [Role.DEF] * 7 + [Role.MID] * 7 + [Role.FWD] * 6
)


def _attr(rng: SeededRng, base: float) -> float:
    """A seeded attribute in [base, base+0.3], clamped to the valid [0,1] range."""
    return min(1.0, max(0.0, rng.uniform(base, base + 0.3)))


def generate_squad(nation_seed: int, tier: int, dna: StyleDNA) -> list[Player]:
    players: list[Player] = []
    for k in range(23):
        rng = SeededRng(sub_seed(nation_seed, "player", k))
        # Stronger tiers (tier 1) sit higher in the band; cap keeps attributes <= 1.
        base = min(0.65, 0.45 + 0.07 * (4 - tier))
        players.append(Player(
            id=f"{nation_seed}-{k}", role=_ROLES[k],
            pace=_attr(rng, base), accel=_attr(rng, base),
            shooting=_attr(rng, base), passing=_attr(rng, base),
            dribbling=_attr(rng, base), vision=_attr(rng, base),
            defending=_attr(rng, base), stamina=_attr(rng, base),
            teamwork=_attr(rng, base), mass=1.0,
        ))
    return players
