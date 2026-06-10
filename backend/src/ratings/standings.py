"""Standings calculation + the ordered tiebreaker chain (deterministic)."""
from __future__ import annotations
from src.domain.tournament import MatchSummary, Standing
from src.seed.provider import sub_seed


def empty_table(group_of: dict[str, str], group: str) -> list[Standing]:
    """A fresh zeroed table for every team assigned to ``group``."""
    return [Standing(team_id=tid, group=group)
            for tid, g in sorted(group_of.items()) if g == group]


def apply_result(table: list[Standing], summary: MatchSummary) -> None:
    """Fold one group-stage result into the table in place."""
    by_id = {s.team_id: s for s in table}
    home, away = by_id.get(summary.home_id), by_id.get(summary.away_id)
    if home is None or away is None:
        return
    for side, gf, ga in ((home, summary.score_home, summary.score_away),
                         (away, summary.score_away, summary.score_home)):
        side.played += 1
        side.gf += gf
        side.ga += ga
        if gf > ga:
            side.w += 1
            side.pts += 3
        elif gf < ga:
            side.l += 1
        else:
            side.d += 1
            side.pts += 1


def order_group(standings: list[Standing], master_seed: int, group_id: str) -> list[Standing]:
    """points -> GD -> GF -> (head-to-head*) -> fair-play -> seeded lot.

    Head-to-head and fair-play are not yet modelled; the final, otherwise-equal
    tie is broken by a deterministic seeded lot so ordering is always stable.
    """
    def key(s: Standing):
        lot = sub_seed(master_seed, "tiebreak", group_id, s.team_id)
        return (-s.pts, -(s.gf - s.ga), -s.gf, lot)
    return sorted(standings, key=key)
