# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

AI Agentic World Cup — a simulated football tournament where AI-driven teams play matches that are **fully deterministic** and reproducible from a single master seed. Two apps plus infra-as-code:

- `backend/` — Python 3.11+ / FastAPI, hexagonal (ports & adapters) architecture.
- `frontend/` — React 18 + Vite + TypeScript, TanStack (Query / Router / Table), SignalR for live match frames.
- `backend/azure/` — Bicep templates (Container Apps, Service Bus, Postgres, Redis, Blob, SignalR).
- `docs/` — `01-c4-overview.md`, `02-comprehensive-architecture.md`, `03-implementation-blueprint.md`. **Read these for design intent**; the code was scaffolded from them.

### Implementation status — important
Originally a scaffold; the **end-to-end tournament pipeline is now implemented and runs** (generation → draw → round-robin groups → standings → knockout bracket → champion), persisting to real local adapters. See `RUN.md` for how to launch it. Remaining `# TODO` / `// TODO` stubs are **intentional** and carry a one-line responsibility — the main ones are the per-player **physics** (`match_engine/physics.py`), the **DecisionPolicy** brains (`match_engine/policies/*`, `behaviors.py`, `team_orchestrator.py`), live **SignalR** frame streaming, and parts of the frontend. The high-level match outcome comes from a deterministic chance model in `match_engine/runtime.py` (physics-light) — when the physics path lands it slots behind the same `run()` boundary. When implementing a TODO, the surrounding signatures and the docs are the spec.

## Commands

Run the whole stack in Docker (from repo root) — see `RUN.md` for details:
```
.\run-local.ps1            # build + start postgres/redis/azurite/api/worker/frontend
.\run-local.ps1 demo       # also simulate a 32-team World Cup and print the champion
.\run-local.ps1 down       # stop
```

Backend (run from `backend/`):
```
pip install -e ".[dev]"                      # install incl. pytest/mypy/ruff
$env:WC_BACKEND="memory"; uvicorn src.app.main:app --reload   # API + in-process workers, no infra
python -m src.workers.main                   # standalone worker (queue consumer; local/azure backends)
pytest                                       # all tests (asyncio_mode=auto)
pytest tests/test_orchestrator_e2e.py        # the end-to-end tournament tests
mypy src                                     # type check
ruff check src                               # lint
```

`WC_BACKEND` selects the adapter set: `memory` (single process, no infra — default, used by tests), `local` (Redis + Postgres + Azurite, the Docker stack), or `azure`. See `app/config.py`.

Frontend (run from `frontend/`):
```
npm install
npm run dev        # Vite dev server; proxies /api -> http://localhost:8000
npm run build      # tsc -b && vite build  (Docker image uses `vite build` only)
```

## Architecture: the two non-negotiable invariants

Everything here exists to protect two properties. When changing code, preserve both.

### 1. Dependencies point inward (hexagonal)
- `domain/` and `match_engine/` depend on **nothing external** — pure, no I/O, no Azure SDK.
- `orchestrator/`, `generation/`, `ratings/` depend only on `domain` + `infra/ports.py`.
- `infra/` adapters (`store_postgres`, `queue_servicebus`, `eventlog_blob`, `cache_redis`, `signalr`, `llm_gateway`) **implement** the `Protocol`s in `infra/ports.py`. They are the only place that imports Azure/Postgres/Redis SDKs.
- `app/deps.py` is the **only** wiring point: it picks a concrete adapter per port from `Settings`. To swap Azure for anything else, re-implement the ports and change `deps.py` — the deterministic core never changes.
- Consequence: never import an `infra/` adapter from `domain`, `match_engine`, `orchestrator`, `generation`, or `ratings`. Depend on the `ports.py` Protocol instead.

### 2. Determinism: identical (seed, config, rules) ⇒ identical run
- **No ambient randomness anywhere in the core.** Never call `random`, `time`, `uuid`, or unseeded sources in `domain`/`match_engine`/`orchestrator`/`generation`. Every random decision must derive from a seed.
- `seed/provider.py::sub_seed(master, *path)` derives a stable 32-bit sub-seed by SHA-256 of the master + a path (e.g. `sub_seed(seed, "nation", 3)`). Use the path to namespace independent random streams so they don't interfere.
- `seed/rng.py::SeededRng` is a plain LCG (chosen for cross-language parity) — the only PRNG the core uses.
- `MatchEngine.simulate(req)` is a pure function of `MatchRequest`; `match_engine/runtime.py` runs a fixed timestep (`FIXED = 1/120`) so physics is reproducible.
- `observability/run_hash.py::run_hash(events)` hashes the ordered event log; equal seeds must produce equal hashes. This is the reproducibility check — preserve event ordering and payload stability when editing the engine. `test_determinism.py` guards this.

## Runtime flow

1. `POST /tournaments` (`api/routes_tournaments.py`) kicks off `TournamentOrchestrator.start` as a FastAPI `BackgroundTask`, using the adapter bundle from `app/deps.py::get_deps()`.
2. `orchestrator/fsm.py::TournamentOrchestrator` is the conductor — a lifecycle FSM stepping `GENERATING → DRAW → GROUP → R16 → QF → SF → FINAL → DONE`. It composes single-responsibility agents: `NationalTeamGenerator`, `DrawAgent`, `SchedulerAgent` (round-robin + knockout fixtures), `MatchDispatcher`, `ProgressionManager` (qualifiers + bracket), `ResultAggregator`, `RunSupervisor` (snapshots to the store).
3. For each matchday/round the orchestrator builds `MatchRequest`s, **enqueues them on the `MatchQueue` port**, then **awaits each result on the `ResultBus` port** (`asyncio.gather`). `workers/match_worker.py` consumes a job, calls the **pure** `MatchEngine.simulate`, appends events to the `EventLog`, and **publishes the result on the `ResultBus`**. The worker owns event-log writes — the orchestrator/aggregator must not re-append (that double-counts).
4. The orchestrator folds results into group `Standing`s (`ratings/standings.py`), advances the bracket, and snapshots the full `Tournament` read-model (teams/fixtures/standings/results/bracket/champion) to the `StateStore`. The API serves it back over REST with **camelCase** DTOs (`api/schemas.py`) to match the frontend types.
5. In `memory` mode the API process runs the workers in-process (see `app/main.py` lifespan); in `local`/`azure` mode the separate `worker` container does. Live SignalR frame streaming is not yet wired locally (replay via `/matches/{id}/events`).

The match-internal AI mirrors the same pattern at a smaller scale: `match_engine/team_orchestrator.py` holds a pluggable `DecisionPolicy` (`policies/base.py` Protocol; `heuristic.py` / `rl.py` implementations) — Strategy pattern, so the team "brain" is swappable without touching the simulation loop.

## Conventions

- Backend: `from __future__ import annotations` at the top of every module; Pydantic v2 for all domain contracts; ports are `typing.Protocol` (structural, not ABCs). Settings bind from env with prefix `WC_` (see `app/config.py`).
- Frontend: data fetching goes through `api/client.ts::http<T>` and TanStack Query hooks in `hooks/`; routes are file-based under `routes/` (TanStack Router). API base is `VITE_API_BASE` (defaults to `/api`).
