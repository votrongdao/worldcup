"""Assemble a validated, rated, match-ready team from squad + coach."""
from __future__ import annotations
from src.domain.player import Player, Role
from src.domain.team import Team, CoachProfile, StyleDNA

# A 4-3-3 starting XI: 1 GK, 4 DEF, 3 MID, 3 FWD.
_XI_SHAPE: dict[Role, int] = {Role.GK: 1, Role.DEF: 4, Role.MID: 3, Role.FWD: 3}


def _pick_xi(squad: list[Player]) -> list[str]:
    """Best available per line by overall attribute sum, falling back to fill 11."""
    def overall(p: Player) -> float:
        return p.defending + p.passing + p.shooting + p.pace + p.vision

    xi: list[str] = []
    for role, count in _XI_SHAPE.items():
        ranked = sorted((p for p in squad if p.role == role), key=overall, reverse=True)
        xi.extend(p.id for p in ranked[:count])
    if len(xi) < 11:  # fill any short line from whoever is left
        chosen = set(xi)
        rest = sorted((p for p in squad if p.id not in chosen), key=overall, reverse=True)
        xi.extend(p.id for p in rest[: 11 - len(xi)])
    return xi[:11]


def build_team(team_id: str, nation: str, tier: int, dna: StyleDNA,
               squad: list[Player], coach: CoachProfile) -> Team:
    xi = _pick_xi(squad)
    rating = sum(p.passing + p.defending + p.shooting for p in squad) / max(len(squad), 1)
    return Team(id=team_id, nation=nation, tier=tier, style_dna=dna,
                rating=rating, squad=squad, xi=xi, coach=coach)
