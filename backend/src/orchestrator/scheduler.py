"""SchedulerAgent: build the fixture list for a round (round-robin / bracket)."""
from __future__ import annotations
from src.domain.tournament import Fixture, Phase


def _round_robin(team_ids: list[str]) -> list[tuple[int, str, str]]:
    """Circle-method round-robin. Returns (matchday, home, away) triples.

    Deterministic: pairings depend only on the (already deterministic) team order.
    """
    teams = list(team_ids)
    if len(teams) % 2:
        teams.append("__bye__")
    n = len(teams)
    days: list[tuple[int, str, str]] = []
    for day in range(n - 1):
        for i in range(n // 2):
            home, away = teams[i], teams[n - 1 - i]
            if "__bye__" in (home, away):
                continue
            # alternate home/away by day so it is not always the same side
            if day % 2:
                home, away = away, home
            days.append((day + 1, home, away))
        teams.insert(1, teams.pop())  # rotate, keeping teams[0] fixed
    return days


class SchedulerAgent:
    name = "scheduler_agent"

    def group_fixtures(self, group_of: dict[str, str]) -> list[Fixture]:
        """Round-robin within each group, in deterministic group/team order."""
        by_group: dict[str, list[str]] = {}
        for team_id, group in sorted(group_of.items()):
            by_group.setdefault(group, []).append(team_id)

        fixtures: list[Fixture] = []
        for group in sorted(by_group):
            for matchday, home, away in _round_robin(sorted(by_group[group])):
                fid = f"g{group}-d{matchday}-{home}-{away}"
                fixtures.append(Fixture(id=fid, phase=Phase.GROUP, home_id=home,
                                        away_id=away, group=group, matchday=matchday))
        return fixtures

    def knockout_fixtures(self, phase: Phase, pairings: list[tuple[str, str]]) -> list[Fixture]:
        """One single-leg fixture per pairing for a knockout round."""
        fixtures: list[Fixture] = []
        for i, (home, away) in enumerate(pairings, start=1):
            fid = f"{phase.value}-m{i}-{home}-{away}"
            fixtures.append(Fixture(id=fid, phase=phase, home_id=home,
                                    away_id=away, matchday=i))
        return fixtures
