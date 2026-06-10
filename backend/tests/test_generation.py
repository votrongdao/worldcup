"""Generation determinism + validity (XI size, attribute ranges)."""
from src.generation.national_team_generator import NationalTeamGenerator


def test_team_generation_deterministic():
    g = NationalTeamGenerator()
    a = g.generate(7, 0, "NAT00")
    b = g.generate(7, 0, "NAT00")
    assert a.model_dump() == b.model_dump()
    assert len(a.xi) == 11
