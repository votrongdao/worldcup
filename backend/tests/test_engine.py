"""Match Engine v2: determinism, decisive knockouts, sane output."""
from src.domain.match import MatchRequest, MatchRules
from src.generation.national_team_generator import NationalTeamGenerator
from src.match_engine.engine import MatchEngine
from src.match_engine.physics import FIELD_L, FIELD_W

_g = NationalTeamGenerator()
_eng = MatchEngine()


def _teams():
    return _g.generate(11, 0, "Alpha"), _g.generate(11, 3, "Beta")


def test_match_is_deterministic():
    h, a = _teams()
    r1 = _eng.simulate(MatchRequest(match_id="m", home=h, away=a, seed=42))
    r2 = _eng.simulate(MatchRequest(match_id="m", home=h, away=a, seed=42))
    assert (r1.score_home, r1.score_away) == (r2.score_home, r2.score_away)
    assert [(e.type, e.t, e.team) for e in r1.events] == [(e.type, e.t, e.team) for e in r2.events]


def test_frames_consistent_and_in_bounds():
    h, a = _teams()
    base = _eng.simulate(MatchRequest(match_id="m", home=h, away=a, seed=7))
    withf = _eng.simulate(MatchRequest(match_id="m", home=h, away=a, seed=7), capture_frames=True)
    assert (base.score_home, base.score_away) == (withf.score_home, withf.score_away)
    assert len(withf.frames) > 50
    for f in withf.frames:
        assert len(f["players"]) == 22
        for px, py in f["players"]:
            assert -2 <= px <= FIELD_L + 2 and -2 <= py <= FIELD_W + 2


def test_knockout_is_decisive():
    h, a = _g.generate(5, 0, "X"), _g.generate(5, 0, "X")  # identical -> likely level
    r = _eng.simulate(MatchRequest(match_id="ko", home=h, away=a, seed=3,
                                   rules=MatchRules(duration=90, extra_time=True, penalties=True)))
    assert r.winner in ("home", "away")


def test_scorelines_are_plausible():
    # A handful of matches should not be absurd (no 0-shot or 50-goal games).
    goals = []
    for s in range(6):
        h, a = _g.generate(20, s, f"H{s}"), _g.generate(20, s + 10, f"A{s}")
        r = _eng.simulate(MatchRequest(match_id=f"m{s}", home=h, away=a, seed=s * 13 + 1))
        goals.append(r.score_home + r.score_away)
        assert r.stats.shots_home + r.stats.shots_away > 0
    assert max(goals) <= 12
