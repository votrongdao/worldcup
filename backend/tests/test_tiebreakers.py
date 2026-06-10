"""Tiebreaker chain: head-to-head, fair-play, and the deterministic seeded lot."""
from src.domain.tournament import MatchSummary, Phase, Standing
from src.ratings.standings import order_group


def _st(tid, pts, gf, ga, fair=0):
    return Standing(team_id=tid, group="A", pts=pts, gf=gf, ga=ga, fair=fair)


def _m(home, away, sh, sa):
    return MatchSummary(match_id=f"{home}{away}", home_id=home, away_id=away,
                        phase=Phase.GROUP, score_home=sh, score_away=sa)


def test_head_to_head_breaks_a_three_way_tie():
    # A, B, C identical on points/GD/GF; head-to-head: A > B > C.
    table = [_st("A", 6, 3, 1), _st("B", 6, 3, 1), _st("C", 6, 3, 1), _st("D", 0, 0, 4)]
    results = [_m("A", "B", 1, 0), _m("A", "C", 1, 0), _m("B", "C", 1, 0)]
    order = [s.team_id for s in order_group(table, results, master_seed=1, group_id="A")]
    assert order == ["A", "B", "C", "D"]


def test_fair_play_breaks_when_head_to_head_is_level():
    # A and B drew each other (h2h level); A has fewer disciplinary demerits.
    table = [_st("A", 4, 2, 2, fair=2), _st("B", 4, 2, 2, fair=6)]
    results = [_m("A", "B", 1, 1)]
    order = [s.team_id for s in order_group(table, results, master_seed=1, group_id="A")]
    assert order == ["A", "B"]


def test_seeded_lot_is_deterministic_and_total():
    # Two teams identical in everything, no head-to-head -> seeded lot decides, stably.
    table = [_st("A", 3, 1, 1), _st("B", 3, 1, 1)]
    o1 = [s.team_id for s in order_group(table, [], master_seed=99, group_id="A")]
    o2 = [s.team_id for s in order_group(table, [], master_seed=99, group_id="A")]
    assert o1 == o2                      # deterministic
    assert sorted(o1) == ["A", "B"]      # a total order over both teams
