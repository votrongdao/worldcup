"""SelfPlayCoordinator: play one fixture on demand, record it, advance the round.

For self-play tournaments (config.auto_play=False) the orchestrator schedules the
fixtures but does not run them — the user plays each match (live or instant) from the
UI. This coordinator simulates a single fixture deterministically, persists its events
+ summary, updates the group table, and — when a round is complete — builds the next
round's fixtures (groups → R16 → QF → SF → final + third-place → done).

Deterministic: the seed is sub_seed(config.seed, "match", fixture.id), exactly as the
auto orchestrator uses, so a self-played match equals its auto-played counterpart.
"""
from __future__ import annotations
import asyncio

from src.domain.match import MatchRequest, MatchResult, MatchRules
from src.domain.tournament import BracketSlot, Fixture, MatchSummary, Phase, Tournament
from src.infra.ports import EventLog, StateStore
from src.match_engine.engine import MatchEngine
from src.ratings.standings import apply_result, empty_table, order_group
from src.seed.provider import sub_seed
from .policy import TournamentPolicy
from .progression import ProgressionManager
from .scheduler import SchedulerAgent
from .supervisor import RunSupervisor

_PHASE_BY_PAIRS = {8: Phase.R16, 4: Phase.QF, 2: Phase.SF, 1: Phase.FINAL}
_KNOCKOUT = (Phase.R16, Phase.QF, Phase.SF, Phase.FINAL, Phase.THIRD_PLACE)


class SelfPlayCoordinator:
    name = "self_play_coordinator"

    def __init__(self, store: StateStore, log: EventLog) -> None:
        self._store = store
        self._log = log
        self._engine = MatchEngine()
        self._sched = SchedulerAgent()
        self._progress = ProgressionManager()
        self._supervisor = RunSupervisor(store)

    # -- request building (shared with the live WS so frames match the record) --
    def fixture(self, t: Tournament, mid: str) -> Fixture | None:
        return next((f for f in t.fixtures if f.id == mid), None)

    def request_for(self, t: Tournament, f: Fixture) -> MatchRequest:
        knockout = f.phase is not Phase.GROUP
        return MatchRequest(
            match_id=f.id, home=t.teams[f.home_id], away=t.teams[f.away_id],
            seed=sub_seed(t.config.seed, "match", f.id),
            rules=MatchRules(duration=90.0, extra_time=knockout, penalties=knockout),
        )

    async def play(self, t: Tournament, mid: str) -> MatchSummary | None:
        """Simulate + record a fixture instantly (no live stream)."""
        f = self.fixture(t, mid)
        if f is None:
            return None
        if mid in t.results:
            return t.results[mid]
        result = self._engine.simulate(self.request_for(t, f))
        return await self.record(t, f, result)

    def current_round(self, t: Tournament) -> list[Fixture]:
        """The fixtures that make up the current 'round' — one group matchday, or the
        whole current knockout phase — so they can be played together."""
        if t.phase is Phase.GROUP:
            group_fx = [f for f in t.fixtures if f.phase is Phase.GROUP]
            days = sorted({f.matchday for f in group_fx if f.id not in t.results})
            if not days:
                return []
            return [f for f in group_fx if f.matchday == days[0]]
        # knockout: the current phase, plus the third-place playoff (played alongside the final)
        phases = {t.phase, Phase.THIRD_PLACE} if t.phase is Phase.FINAL else {t.phase}
        return [f for f in t.fixtures if f.phase in phases]

    async def play_round(self, t: Tournament) -> int:
        """Play every unplayed fixture in the current round in parallel, then update
        tables + advance once. Returns how many matches were played."""
        pending = [f for f in self.current_round(t) if f.id not in t.results]
        if not pending:
            return 0
        results = await asyncio.gather(
            *(asyncio.to_thread(self._engine.simulate, self.request_for(t, f)) for f in pending)
        )
        groups: set[str] = set()
        for f, result in zip(pending, results):
            await self._log.append(f.id, result.events)
            self._apply(t, f, result)
            if f.group:
                groups.add(f.group)
        for g in groups:
            self._recompute_group(t, g)
        self._advance(t)
        await self._supervisor.snapshot(t)
        return len(pending)

    async def play_all(self, t: Tournament) -> int:
        """Keep playing rounds until the tournament is finished (runs in the background;
        each round is snapshotted so a polling UI shows it progress)."""
        total = 0
        for _ in range(80):                          # safety bound (32-team cup ≈ 7 rounds)
            if t.phase is Phase.DONE:
                break
            n = await self.play_round(t)
            if n == 0:
                break
            total += n
        return total

    def _apply(self, t: Tournament, f: Fixture, result: MatchResult) -> None:
        """Resolve + persist a single summary (no standings/advance — caller batches those)."""
        if f.phase is not Phase.GROUP:
            result = TournamentPolicy(t.config.seed).resolve_draw(result, f.id)
        winner_id = (f.home_id if result.winner == "home"
                     else f.away_id if result.winner == "away" else None)
        t.results[f.id] = MatchSummary(
            match_id=f.id, home_id=f.home_id, away_id=f.away_id, phase=f.phase,
            score_home=result.score_home, score_away=result.score_away,
            decided_by=result.decided_by, winner_id=winner_id,
            fairplay_home=result.stats.fairplay_home, fairplay_away=result.stats.fairplay_away,
        )
        if f.phase is not Phase.GROUP:
            t.bracket = [b for b in t.bracket if b.match_id != f.id]
            t.bracket.append(BracketSlot(match_id=f.id, phase=f.phase, home_id=f.home_id,
                                         away_id=f.away_id, winner_id=winner_id))

    async def record(self, t: Tournament, f: Fixture, result: MatchResult) -> MatchSummary:
        """Persist a (possibly already-simulated) result and advance the tournament."""
        if f.id in t.results:
            return t.results[f.id]
        await self._log.append(f.id, result.events)        # event log (replay/report/commentary)
        self._apply(t, f, result)
        if f.group:
            self._recompute_group(t, f.group)
        self._advance(t)
        await self._supervisor.snapshot(t)
        return t.results[f.id]

    # ----------------------------------------------------------------- internals
    def _recompute_group(self, t: Tournament, g: str) -> None:
        table = empty_table(t.group_of, g)
        played = [t.results[f.id] for f in t.fixtures
                  if f.group == g and f.id in t.results]
        for s in played:
            apply_result(table, s)
        t.standings[g] = order_group(table, played, t.config.seed, g)

    def _done(self, t: Tournament, fixtures: list[Fixture]) -> bool:
        return bool(fixtures) and all(f.id in t.results for f in fixtures)

    def _phase_fixtures(self, t: Tournament, phase: Phase) -> list[Fixture]:
        return [f for f in t.fixtures if f.phase is phase]

    def _has(self, t: Tournament, phase: Phase) -> bool:
        return any(f.phase is phase for f in t.fixtures)

    def _advance(self, t: Tournament) -> None:
        """Schedule the next round when the current one is complete; finalize at the end."""
        # group stage -> seed the knockout bracket
        if t.phase is Phase.GROUP:
            if self._done(t, self._phase_fixtures(t, Phase.GROUP)):
                qual = self._progress.qualifiers(t.standings, t.config.advance_per_group)
                pairings = self._progress.build_bracket(qual)
                phase = _PHASE_BY_PAIRS.get(len(pairings), Phase.FINAL)
                t.fixtures.extend(self._sched.knockout_fixtures(phase, pairings))
                t.phase = phase
            return

        # final stage: champion / runner-up / third place, then DONE
        final_fx = self._phase_fixtures(t, Phase.FINAL)
        if final_fx:
            f = final_fx[0]
            if f.id in t.results:
                s = t.results[f.id]
                t.champion_id = s.winner_id
                t.runner_up_id = f.away_id if s.winner_id == f.home_id else f.home_id
            third = self._phase_fixtures(t, Phase.THIRD_PLACE)
            if third and third[0].id in t.results:
                t.third_place_id = t.results[third[0].id].winner_id
            final_done = f.id in t.results
            third_done = (not third) or third[0].id in t.results
            if final_done and third_done:
                t.run_hash = self._run_hash(t)
                t.phase = Phase.DONE
            return

        # R16 / QF / SF — advance the first complete round whose successor isn't scheduled
        for phase in (Phase.R16, Phase.QF, Phase.SF):
            cur = self._phase_fixtures(t, phase)
            if not cur:
                continue
            if not self._done(t, cur):
                t.phase = phase
                return
            winners = [t.results[f.id].winner_id for f in cur if t.results[f.id].winner_id]
            if phase is Phase.SF:
                if not self._has(t, Phase.FINAL):
                    losers = [(f.away_id if t.results[f.id].winner_id == f.home_id else f.home_id)
                              for f in cur]
                    t.fixtures.extend(self._sched.knockout_fixtures(
                        Phase.FINAL, [(winners[0], winners[1])]))
                    if t.config.third_place and len(losers) == 2:
                        t.fixtures.extend(self._sched.knockout_fixtures(
                            Phase.THIRD_PLACE, [(losers[0], losers[1])]))
                    t.phase = Phase.FINAL
                return
            next_pairings = self._progress.advance([], winners)
            next_phase = _PHASE_BY_PAIRS.get(len(next_pairings), Phase.FINAL)
            if not self._has(t, next_phase):
                t.fixtures.extend(self._sched.knockout_fixtures(next_phase, next_pairings))
                t.phase = next_phase
            return

    @staticmethod
    def _run_hash(t: Tournament) -> str:
        import hashlib
        h = hashlib.sha256()
        for f in t.fixtures:
            s = t.results.get(f.id)
            if s is None:
                continue
            h.update(f"{f.id}:{s.score_home}:{s.score_away}:{s.decided_by}:{s.winner_id}".encode())
        return h.hexdigest()
