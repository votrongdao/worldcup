"""TournamentOrchestrator: the top-level lifecycle state machine (the conductor)."""
from __future__ import annotations
import asyncio
import hashlib

from src.domain.match import MatchRequest, MatchRules
from src.domain.tournament import (
    BracketSlot,
    Fixture,
    MatchSummary,
    Phase,
    Tournament,
    TournamentConfig,
)
from src.infra.ports import EventLog, LlmGateway, MatchQueue, ResultBus, StateStore
from src.generation.national_team_generator import NationalTeamGenerator
from src.generation.nations import nation_name
from src.ratings.standings import apply_result, empty_table, order_group
from src.seed.provider import sub_seed
from .aggregator import ResultAggregator
from .dispatcher import MatchDispatcher
from .draw import DrawAgent
from .progression import ProgressionManager
from .scheduler import SchedulerAgent
from .supervisor import RunSupervisor

# Number of knockout pairings -> the round that many pairings constitutes.
_PHASE_BY_PAIRS = {8: Phase.R16, 4: Phase.QF, 2: Phase.SF, 1: Phase.FINAL}


class TournamentOrchestrator:
    name = "tournament_orchestrator"

    def __init__(self, queue: MatchQueue, store: StateStore, log: EventLog,
                 bus: ResultBus, llm: LlmGateway | None = None) -> None:
        self._store = store
        self._bus = bus
        self._gen = NationalTeamGenerator()
        self._draw = DrawAgent()
        self._sched = SchedulerAgent()
        self._dispatch = MatchDispatcher(queue)
        self._progress = ProgressionManager()
        self._aggregate = ResultAggregator(log, llm)
        self._supervisor = RunSupervisor(store)

    async def start(self, config: TournamentConfig) -> Tournament:
        t = Tournament(id=f"wc-{config.seed}", config=config)

        t.phase = Phase.GENERATING
        teams = [self._gen.generate(config.seed, i, nation_name(i))
                 for i in range(config.teams)]
        t.teams = {tm.id: tm for tm in teams}

        t.phase = Phase.DRAW
        t.group_of = self._draw.draw(config.seed, teams, config.groups)
        await self._supervisor.snapshot(t)

        t.phase = Phase.GROUP
        await self._run_group_stage(t)
        await self._supervisor.snapshot(t)

        await self._run_knockouts(t)

        t.run_hash = self._run_hash(t)
        t.phase = Phase.DONE
        await self._supervisor.snapshot(t)
        return t

    # ------------------------------------------------------------------ #
    async def _run_group_stage(self, t: Tournament) -> None:
        fixtures = self._sched.group_fixtures(t.group_of)
        t.fixtures.extend(fixtures)

        groups = sorted(set(t.group_of.values()))
        tables = {g: empty_table(t.group_of, g) for g in groups}

        by_day: dict[int, list[Fixture]] = {}
        for f in fixtures:
            by_day.setdefault(f.matchday, []).append(f)

        # Matchdays run in order; all fixtures within a matchday run in parallel.
        for day in sorted(by_day):
            for fixture, summary in await self._play(t, by_day[day], knockout=False):
                if fixture.group:
                    apply_result(tables[fixture.group], summary)

        t.standings = {g: order_group(tables[g], t.config.seed, g) for g in groups}

    async def _run_knockouts(self, t: Tournament) -> None:
        qual = self._progress.qualifiers(t.standings, t.config.advance_per_group)
        pairings = self._progress.build_bracket(qual)

        while pairings:
            phase = _PHASE_BY_PAIRS.get(len(pairings), Phase.FINAL)
            t.phase = phase
            fixtures = self._sched.knockout_fixtures(phase, pairings)
            t.fixtures.extend(fixtures)

            played = await self._play(t, fixtures, knockout=True)
            for fixture, summary in played:
                t.bracket.append(BracketSlot(
                    match_id=fixture.id, phase=phase, home_id=fixture.home_id,
                    away_id=fixture.away_id, winner_id=summary.winner_id))

            winners = [summary.winner_id for _, summary in played if summary.winner_id]
            if len(winners) <= 1:
                t.champion_id = winners[0] if winners else None
                break
            pairings = self._progress.advance(pairings, winners)
            await self._supervisor.snapshot(t)

    # ------------------------------------------------------------------ #
    async def _play(self, t: Tournament, fixtures: list[Fixture],
                    knockout: bool) -> list[tuple[Fixture, MatchSummary]]:
        """Dispatch a batch of fixtures, await their results, persist summaries."""
        rules = MatchRules(duration=90.0, extra_time=knockout, penalties=knockout)
        requests = [
            MatchRequest(
                match_id=f.id, home=t.teams[f.home_id], away=t.teams[f.away_id],
                seed=sub_seed(t.config.seed, "match", f.id), rules=rules, render=False,
            )
            for f in fixtures
        ]
        await self._dispatch.dispatch(requests)
        results = await asyncio.gather(*(self._bus.result(r.match_id) for r in requests))

        played: list[tuple[Fixture, MatchSummary]] = []
        for fixture, result in zip(fixtures, results):
            await self._aggregate.ingest(result)
            winner_id = (fixture.home_id if result.winner == "home"
                         else fixture.away_id if result.winner == "away" else None)
            summary = MatchSummary(
                match_id=fixture.id, home_id=fixture.home_id, away_id=fixture.away_id,
                phase=fixture.phase, score_home=result.score_home,
                score_away=result.score_away, decided_by=result.decided_by,
                winner_id=winner_id,
            )
            t.results[fixture.id] = summary
            played.append((fixture, summary))
        return played

    @staticmethod
    def _run_hash(t: Tournament) -> str:
        """Stable digest of every result in fixture order — the reproducibility check."""
        h = hashlib.sha256()
        for f in t.fixtures:
            s = t.results.get(f.id)
            if s is None:
                continue
            h.update(f"{f.id}:{s.score_home}:{s.score_away}:{s.decided_by}:{s.winner_id}".encode())
        return h.hexdigest()
