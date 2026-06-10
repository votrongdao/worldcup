"""End-to-end: a tournament runs to completion deterministically in memory mode."""
import asyncio

import pytest

import src.infra.memory as memory
from src.app.deps import get_deps
from src.domain.tournament import Phase, TournamentConfig
from src.orchestrator.fsm import TournamentOrchestrator
from src.workers.main import worker_loop


async def _run(seed: int, teams: int, groups: int):
    # Fresh in-memory backend per run so queues/stores don't leak between cases.
    memory._SINGLETON = None
    get_deps.cache_clear()
    deps = get_deps()
    workers = [asyncio.create_task(worker_loop(deps, name=f"w{i}")) for i in range(4)]
    try:
        orch = TournamentOrchestrator(deps.queue, deps.store, deps.log, deps.bus, deps.llm)
        cfg = TournamentConfig(teams=teams, groups=groups, per_group=teams // groups,
                               advance_per_group=2, seed=seed)
        return await orch.start(cfg)
    finally:
        for w in workers:
            w.cancel()


# Small tournaments keep the (now physics-heavy) engine fast in CI; the structure
# is identical to a 32-team cup, just fewer rounds.
@pytest.mark.asyncio
async def test_tournament_completes():
    t = await _run(seed=2026, teams=8, groups=2)
    assert t.phase is Phase.DONE
    assert t.champion_id in t.teams
    # 2 groups x 6 round-robin matches + SF(2) + Final(1).
    assert len(t.results) == 12 + 3
    phases = [b.phase for b in t.bracket]
    assert phases.count(Phase.SF) == 2
    assert phases.count(Phase.FINAL) == 1
    assert all(len(table) == 4 for table in t.standings.values())


@pytest.mark.asyncio
async def test_run_is_deterministic():
    a = await _run(seed=7, teams=8, groups=2)
    b = await _run(seed=7, teams=8, groups=2)
    assert a.run_hash == b.run_hash
    assert a.champion_id == b.champion_id

    c = await _run(seed=8, teams=8, groups=2)
    assert c.run_hash != a.run_hash
