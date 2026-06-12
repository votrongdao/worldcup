"""Self-play: scheduling without auto-run, on-demand play, and round advancement.

Key invariant: a self-played tournament equals its auto-played twin (same per-match
seed) — same champion and run hash."""
import asyncio

import pytest

import src.infra.memory as memory
from src.app.deps import get_deps
from src.domain.tournament import Phase, TournamentConfig
from src.orchestrator.fsm import TournamentOrchestrator
from src.orchestrator.selfplay import SelfPlayCoordinator
from src.workers.main import worker_loop


def _fresh():
    memory._SINGLETON = None
    get_deps.cache_clear()
    return get_deps()


async def _auto(seed, teams, groups):
    deps = _fresh()
    workers = [asyncio.create_task(worker_loop(deps, name=f"w{i}")) for i in range(4)]
    try:
        orch = TournamentOrchestrator(deps.queue, deps.store, deps.log, deps.bus,
                                      deps.llm, deps.events, deps.cache)
        cfg = TournamentConfig(teams=teams, groups=groups, per_group=teams // groups,
                               advance_per_group=2, seed=seed)
        return await orch.start(cfg)
    finally:
        for w in workers:
            w.cancel()


async def _selfplay(seed, teams, groups):
    deps = _fresh()
    orch = TournamentOrchestrator(deps.queue, deps.store, deps.log, deps.bus,
                                  deps.llm, deps.events, deps.cache)
    cfg = TournamentConfig(teams=teams, groups=groups, per_group=teams // groups,
                           advance_per_group=2, seed=seed, auto_play=False)
    t = await orch.start(cfg)               # stops at GROUP, fixtures scheduled, nothing played
    coord = SelfPlayCoordinator(deps.store, deps.log)
    return t, coord


@pytest.mark.asyncio
async def test_selfplay_schedules_but_does_not_run():
    t, _ = await _selfplay(2026, 8, 2)
    assert t.phase is Phase.GROUP
    assert len(t.fixtures) == 12          # 2 groups x 6 round-robin fixtures
    assert len(t.results) == 0            # nothing played yet
    assert all(len(table) == 4 for table in t.standings.values())   # empty tables shown


@pytest.mark.asyncio
async def test_selfplay_play_records_and_updates_table():
    t, coord = await _selfplay(2026, 8, 2)
    f = t.fixtures[0]
    summary = await coord.play(t, f.id)
    assert summary is not None and f.id in t.results
    # the played team(s) now show 1 game in the table
    played_rows = [s for tbl in t.standings.values() for s in tbl if s.played > 0]
    assert len(played_rows) == 2
    # idempotent: replaying returns the same summary, no double count
    again = await coord.play(t, f.id)
    assert (again.score_home, again.score_away) == (summary.score_home, summary.score_away)


@pytest.mark.asyncio
async def test_selfplay_completes_like_autoplay():
    auto = await _auto(2026, 8, 2)
    t, coord = await _selfplay(2026, 8, 2)

    # Play every scheduled fixture; new rounds appear as each completes.
    for _ in range(50):
        if t.phase is Phase.DONE:
            break
        pending = [f for f in t.fixtures if f.id not in t.results]
        if not pending:
            break
        for f in pending:
            await coord.play(t, f.id)

    assert t.phase is Phase.DONE
    assert t.champion_id == auto.champion_id
    assert t.run_hash == auto.run_hash               # self-play == auto-play
    assert t.third_place_id == auto.third_place_id
