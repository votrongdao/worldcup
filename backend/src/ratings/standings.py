"""Standings calculation + the full, ordered tiebreaker chain (deterministic)."""
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
    home.fair += summary.fairplay_home
    away.fair += summary.fairplay_away
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


def _head_to_head(team_ids: set[str], results: list[MatchSummary]) -> dict[str, tuple[int, int, int]]:
    """Mini-table (pts, gf, ga) over matches played ONLY among ``team_ids``."""
    h2h = {tid: [0, 0, 0] for tid in team_ids}
    for r in results:
        if r.home_id in team_ids and r.away_id in team_ids:
            h2h[r.home_id][1] += r.score_home
            h2h[r.home_id][2] += r.score_away
            h2h[r.away_id][1] += r.score_away
            h2h[r.away_id][2] += r.score_home
            if r.score_home > r.score_away:
                h2h[r.home_id][0] += 3
            elif r.score_away > r.score_home:
                h2h[r.away_id][0] += 3
            else:
                h2h[r.home_id][0] += 1
                h2h[r.away_id][0] += 1
    return {tid: tuple(v) for tid, v in h2h.items()}


def order_group(standings: list[Standing], results: list[MatchSummary],
                master_seed: int, group_id: str) -> list[Standing]:
    """Order a group: points -> GD -> GF -> head-to-head -> fair-play -> seeded lot.

    Teams equal on (points, GD, GF) form a cluster resolved by a head-to-head
    mini-table among themselves, then by fewer fair-play demerits, then by a stable
    seeded lot so the result is always deterministic.
    """
    def primary(s: Standing):
        return (-s.pts, -(s.gf - s.ga), -s.gf)

    ordered = sorted(standings, key=primary)
    out: list[Standing] = []
    i = 0
    while i < len(ordered):
        j = i
        while j + 1 < len(ordered) and primary(ordered[j + 1]) == primary(ordered[i]):
            j += 1
        cluster = ordered[i:j + 1]
        if len(cluster) > 1:
            ids = {s.team_id for s in cluster}
            h2h = _head_to_head(ids, results)

            def key(s: Standing):
                pts, gf, ga = h2h[s.team_id]
                lot = sub_seed(master_seed, "tiebreak", group_id, s.team_id)
                return (-pts, -(gf - ga), -gf, s.fair, lot)  # fewer demerits first

            cluster = sorted(cluster, key=key)
        out.extend(cluster)
        i = j + 1
    return out
