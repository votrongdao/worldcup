"""The tactical replay must be deterministic and stay on the pitch."""
from src.generation.national_team_generator import NationalTeamGenerator
from src.match_engine.physics import FIELD_L, FIELD_W
from src.match_engine.replay import generate_frames


def _two_teams():
    g = NationalTeamGenerator()
    return g.generate(7, 0, "Alpha"), g.generate(7, 1, "Beta")


def test_frames_are_deterministic_and_in_bounds():
    home, away = _two_teams()
    goals = [(23.0, "home"), (61.0, "away"), (78.0, "home")]
    a = generate_frames(home, away, seed=99, goals=goals, duration=90.0)
    b = generate_frames(home, away, seed=99, goals=goals, duration=90.0)
    assert a == b                                  # deterministic
    assert len(a) > 100
    for frame in a:
        assert len(frame["players"]) == 22
        for px, py in frame["players"]:
            assert -3 <= px <= FIELD_L + 3
            assert -1 <= py <= FIELD_W + 1
        bx, by = frame["ball"]
        assert -1 <= bx <= FIELD_L + 1 and -1 <= by <= FIELD_W + 1


def test_no_goals_still_produces_frames():
    home, away = _two_teams()
    frames = generate_frames(home, away, seed=1, goals=[], duration=90.0)
    assert len(frames) > 100
    assert all(len(f["players"]) == 22 for f in frames)
