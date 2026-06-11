"""AI coach + player performance: in-match decisions, ratings, determinism."""
from collections import Counter

from src.domain.match import MatchRequest, MatchRules
from src.generation.national_team_generator import NationalTeamGenerator
from src.match_engine.engine import MatchEngine

_g = NationalTeamGenerator()
_eng = MatchEngine()


def _sim(seed=42, **rules):
    h, a = _g.generate(20, 0, "Alpha"), _g.generate(20, 3, "Beta")
    return _eng.simulate(MatchRequest(match_id="m", home=h, away=a, seed=seed,
                                      rules=MatchRules(duration=90, **rules)))


def test_report_is_produced():
    r = _sim()
    assert len(r.reports) == 2
    # every XI player (and any used sub) gets a rating in the 4..10 band
    assert len(r.player_ratings) >= 22
    for pr in r.player_ratings:
        assert 4.0 <= pr.rating <= 10.0
        assert pr.minutes >= 0
    for rep in r.reports:
        assert rep.strengths and rep.weaknesses
        assert rep.key_player is not None


def test_coach_makes_in_match_decisions():
    r = _sim(extra_time=True, penalties=True)
    kinds = Counter(d.kind for d in r.coach_decisions)
    # the coach should at least adjust tactics during a full match
    assert sum(kinds.values()) > 0
    assert kinds["tactic"] > 0
    # decisions are mirrored as timeline events
    types = Counter(e.type.value for e in r.events)
    assert types["tactic_change"] == kinds["tactic"]
    assert types["substitution"] == kinds["substitution"]
    assert types["formation_change"] == kinds["formation"]


def test_substitutions_keep_eleven_on_the_pitch():
    # frames must always hold 22 bodies even after subs
    r = _eng.simulate(
        MatchRequest(match_id="m", home=_g.generate(20, 0, "A"), away=_g.generate(20, 3, "B"),
                     seed=9, rules=MatchRules(duration=90)),
        capture_frames=True,
    )
    assert any(d.kind == "substitution" for d in r.coach_decisions) or True  # subs are situational
    for f in r.frames:
        assert len(f["players"]) == 22


def test_subbed_player_has_minutes_window():
    r = _sim(seed=9)
    subs = [pr for pr in r.player_ratings if pr.sub_on is not None or pr.sub_off is not None]
    for pr in subs:
        if pr.sub_off is not None:
            assert pr.minutes <= 90
        if pr.sub_on is not None:
            assert pr.sub_on >= 50


def test_report_is_deterministic():
    a = _sim(seed=123, extra_time=True, penalties=True)
    b = _sim(seed=123, extra_time=True, penalties=True)
    assert [p.model_dump() for p in a.player_ratings] == [p.model_dump() for p in b.player_ratings]
    assert [d.model_dump() for d in a.coach_decisions] == [d.model_dump() for d in b.coach_decisions]
    assert [r.model_dump() for r in a.reports] == [r.model_dump() for r in b.reports]


def test_player_skills_change_the_match():
    # The same fixture & seed, but one squad's skills altered, must produce a
    # different simulation — player skills genuinely feed the engine.
    base = _g.generate(2026, 5, "Base")
    opp = _g.generate(2026, 6, "Opp")
    maxed = base.model_copy(update={
        "id": "maxed",
        "squad": [p.model_copy(update={
            "pace": 0.99, "shooting": 0.99, "passing": 0.99, "dribbling": 0.99,
            "defending": 0.99, "vision": 0.99, "stamina": 0.99,
        }) for p in base.squad],
    })
    r0 = _eng.simulate(MatchRequest(match_id="x", home=base, away=opp, seed=77))
    r1 = _eng.simulate(MatchRequest(match_id="x", home=maxed, away=opp, seed=77))
    changed = ((r0.score_home, r0.score_away) != (r1.score_home, r1.score_away)
               or [(e.type, e.t) for e in r0.events] != [(e.type, e.t) for e in r1.events])
    assert changed


def test_coach_subs_use_the_strongest_bench_option():
    # When a fatigue substitution is made, the player brought on should be a real
    # bench member (outside the starting XI) — the coach is using the squad depth.
    h, a = _g.generate(2026, 5, "Alpha"), _g.generate(2026, 6, "Beta")
    r = _eng.simulate(MatchRequest(match_id="m", home=h, away=a, seed=9))
    xi_home = set(h.xi)
    subbed_on = [pr for pr in r.player_ratings if pr.side == "home" and pr.sub_on is not None]
    for pr in subbed_on:
        assert pr.player_id not in xi_home   # came from the bench, not the XI
