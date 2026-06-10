"""ProgressionManager: qualifiers, bracket construction, advancement."""
from __future__ import annotations
from src.domain.tournament import Standing


class ProgressionManager:
    def qualifiers(self, group_standings: dict[str, list[Standing]], n: int) -> dict[str, list[str]]:
        """Top-n team ids per group (tables are assumed already ordered)."""
        return {group: [s.team_id for s in table[:n]]
                for group, table in sorted(group_standings.items())}

    def build_bracket(self, qualifiers: dict[str, list[str]]) -> list[tuple[str, str]]:
        """Seed knockout pairings: winners cross with runners-up of adjacent groups.

        Classic World-Cup crossing for 8 groups A..H advancing 2:
            A1-B2, C1-D2, E1-F2, G1-H2, B1-A2, D1-C2, F1-E2, H1-G2.
        Generalises to any even group count advancing 2; falls back to a flat
        seed pairing (1 vs last) when only one team advances per group.
        """
        groups = sorted(qualifiers)
        advance = max((len(v) for v in qualifiers.values()), default=0)

        if advance >= 2 and len(groups) % 2 == 0:
            pairings: list[tuple[str, str]] = []
            for i in range(0, len(groups), 2):
                g1, g2 = groups[i], groups[i + 1]
                pairings.append((qualifiers[g1][0], qualifiers[g2][1]))  # G1.1 vs G2.2
                pairings.append((qualifiers[g2][0], qualifiers[g1][1]))  # G2.1 vs G1.2
            return pairings

        # Single-qualifier (or odd groups): standard 1-vs-N serpentine seeding.
        seeds = [qualifiers[g][0] for g in groups]
        return [(seeds[i], seeds[len(seeds) - 1 - i]) for i in range(len(seeds) // 2)]

    def advance(self, pairings: list[tuple[str, str]], winners: list[str]) -> list[tuple[str, str]]:
        """Pair this round's winners (in order) into the next round's fixtures."""
        return [(winners[i], winners[i + 1]) for i in range(0, len(winners) - 1, 2)]
