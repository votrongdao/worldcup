# Master Plan — Closing the Architecture Gaps (branch `all-features`)

**Status:** Plan v1 · **Branch:** `all-features` (off `dev`) · **Owner:** core
**Goal:** Bring the implementation into full conformance with the architecture
(`docs/01-c4-overview.md`, `docs/03-implementation-blueprint.md`) by closing every
deviation found in the conformance review, in a professional, test-gated, incremental way.

This plan is the single source of truth for the `all-features` effort. Each workstream
(WS) is independently shippable behind tests and merges to `dev` via PR.

---

## 1. Executive summary

The skeleton and core invariants (hexagonal ports/adapters, determinism, lifecycle FSM,
generation, queue/worker dispatch, persistence, frontend) already conform. The remaining
work is **substance**, not scaffolding:

| # | Gap (from review) | Workstream | Severity |
|---|---|---|---|
| 1 | Match result comes from a **chance model**, not the physics + Team-Orchestrator loop the architecture mandates | **WS1 — Match Engine v2** | 🔴 |
| 2 | **Agent runtime** (`Agent`/`Tool`/`RunContext`, registries) defined but unused; no event bus | **WS2 — Agentic core** | 🟠 |
| 3 | **Blackboard** defined but unused; state is in-RAM, not a shared SSOT | **WS2 — Agentic core** | 🟠 |
| 4 | No **third-place playoff** (config flag ignored) | **WS3 — Tournament rules** | 🟡 |
| 5 | **Tiebreakers** incomplete (no head-to-head / fair-play); tiebreaker test is a stub | **WS3 — Tournament rules** | 🟠 |
| 6 | Knockout draws resolved inside the engine, not via `TournamentPolicy.resolve_draw` | **WS3 — Tournament rules** | 🟡 |
| 7 | **Live frame streaming** not wired (no SignalR locally); live match view inert | **WS4 — Live viewing** | 🟡 |
| 8 | **Azure-native adapters** (Service Bus, SignalR) are stubs; `WC_BACKEND=azure` non-functional | **WS6 — Cloud parity** | 🟡 |
| 9 | `winprob` unused, **golden-master** test stub, **pause/resume** returns 501 | **WS3 / WS5** | 🟡 |
| 10 | Small layering leak: `api` imports `match_engine` directly for replay | **WS1 (boundary)** | 🟡 |

The centrepiece is **WS1**: port the real 2D simulation in `frontend/match.html` into a
deterministic Python Match Engine that produces **both the result and the frames** from a
single seeded run — exactly the "headless + rendered, one codebase" intent of blueprint §6.

---

## 2. Reference asset — `frontend/match.html`

`match.html` is a complete, self-contained 2D football sim and the design reference for
WS1 (engine) and WS4 (live UI). It already implements what the architecture's *Match Engine
Service* (C4 §5.3) describes:

- **Free-rolling ball** that travels ahead of the dribbler (interceptable, winnable).
- **Acceleration-based movement** (arrive-steering, capped speed, player–player separation).
- **Per-player utility decisions** every ~0.18 s: carrier chooses shoot / pass / dribble;
  off-ball players press / mark / support / make onside runs / overlap.
- **Tackles → turnovers or fouls**, pass-lock to prevent instant re-possession.
- **Offside** (second-last defender line + break-the-trap), **fouls**, **yellow/red, send-off**.
- **Dead-ball logic**: kickoff, goal kick, free kick, **penalty**.
- **Coach loop**: formations + tactical styles, auto-coach reacting to score / man-down.
- **Half-time** side switch; **HUD** with score, clock, per-team formation & style selectors.

It maps cleanly onto the design's components: `Match Orchestrator` (clock, restarts, ET/pens),
`Simulation Runtime` (fixed-timestep loop), `Physics Engine`, two `Team Orchestrator`s
(coach slow loop + per-player fast loop), `Event Recorder`.

### 2.1 English tactics mapping (required — source uses Vietnamese labels)

All tactical labels become English. Style parameter vectors are carried over verbatim.

| `match.html` label (VI) | English label | Maps to `StyleDNA` |
|---|---|---|
| `Chồng biên (Overlap)` | **Overlap** | `direct` |
| `Tiki-taka` | **Tiki-Taka** | `possession` |
| `Tổng lực (Total)` | **Total Football** | `high_press` |
| `Phòng ngự (Defensive)` | **Defensive** | `balanced` (low line) |
| `Phòng ngự phản công` | **Counter-Attack** | `counter` |
| `Tấn công & giữ bóng` | **Possession Attack** | `possession` |

Formation keys (`4-4-2`, `4-3-3`, `4-2-3-1`, `3-5-2`, `5-3-2`, `3-4-3`, `5-3-1`) are already
English and carry over unchanged. Style parameter set per style:
`{ line, press, width, overlap, possess, passLen, compact, counter, tempo, aggr }`.

> **Rule:** No Vietnamese strings anywhere in shipped code or UI. A CI grep guards this
> (`scripts/check_english.py` fails the build on non-ASCII tactical labels).

---

## 3. Workstreams

Each WS lists **objective · scope/files · approach · acceptance criteria · tests · risks**.

### WS1 — Deterministic Match Engine v2 (port `match.html`) 🔴

**Objective.** Replace the chance model as the authoritative engine. One seeded run yields
`MatchResult` (score, decisive winner, events) **and** the frame stream. Physics + two Team
Orchestrators produce the outcome, per C4 §5.3.

**Scope / files (`backend/src/match_engine/`):**
- `world.py` — `Body`, `Player` runtime bodies, `Ball` (carrier, kickLock, offsideMark), `MatchWorldState` (players, ball, score, clock, half, state, cards).
- `physics.py` — arrive-steering, speed cap, integration, player separation, ball roll/damping, boundary + goal-line detection. *(extend the existing helpers)*
- `behaviors.py` — formation slots (7 formations), carrier `decideAction` (shoot/pass/dribble utilities), off-ball support/overlap/mark, GK target, kicks (pass/shoot/clear), offside test, dead-ball placement.
- `tactics.py` *(new)* — `FORMATIONS`, `STYLES` (English), `TacticalStyle` dataclass; `StyleDNA → style` resolver so generated teams inherit tactics.
- `policies/heuristic.py` — the per-player fast loop as a `DecisionPolicy`.
- `policies/rl.py` — keep the pluggable stub interface intact.
- `team_orchestrator.py` — coach slow loop (`coach_plan`, auto-react) + `orchestrate` (fast loop) behind the policy.
- `match_orchestrator.py` *(new)* — owns clock, kickoff, restarts, **regulation → extra time → penalty shootout** so the tournament always gets a decisive result (C4 §8.1 note).
- `runtime.py` — fixed-timestep accumulator (`DT = 1/60`, substeps), drives orchestrators + physics, feeds `EventRecorder`, samples frames.
- `recorder.py` — `MatchEvent` log **and** a frame sink (downsampled positions for replay).
- `engine.py` — `MatchEngine.simulate(req) -> MatchResult` (+ optional frame capture flag).

**Approach.**
1. **Determinism first.** Replace every `Math.random()` with `SeededRng(req.seed)` draws.
   Fix all iteration to ordered lists (no set/dict iteration affecting outcomes). Seed the
   coach loop and foul/tackle rolls from the same stream. Add `observability/run_hash` coverage.
2. **Port mechanics** from `match.html` section by section (AI → kicks → control/tackles/fouls
   → dead-ball → physics → coach), translating JS to typed Python, keeping the exact constants.
3. **Headless performance.** Run without rendering; sample frames every ~6 sim-seconds. Target:
   a full 32-team cup (63 matches) completes in **seconds–low minutes** headless (arch §12).
   Bulk tournament stores only results+events; frames are **regenerated on demand** from the
   seed (idempotent), so storage stays small.
4. **Boundary fix (gap #10).** Replace the chance-model `replay.py` with the real engine's frame
   capture. Expose frames through a use-case in `orchestrator` (or a `ReplayService` port), so
   `api` no longer imports `match_engine` directly.

**Acceptance criteria.**
- Same `(home, away, seed, rules)` → identical score, event log, **and** frames (hash-stable).
- Score distribution across 500 seeds is realistic (mean ≈ 1.2–1.6 goals/team; <2 % 0-0 in KO).
- Knockouts always return a decisive winner (ET then penalties).
- `test_match_engine_golden.py` records a baseline and asserts byte-stable event logs.
- A full cup runs headless under the perf budget in CI.

**Tests.** `test_determinism` (run-hash), `test_match_engine_golden`, `test_engine_realism`
(score distribution bounds), `test_knockout_decisive`.

**Risks.** *Realism tuning* (mitigate: constants come straight from the working demo; add
distribution tests). *Performance* of 60 fps × 22 bodies × 63 matches (mitigate: headless,
coarse frame sampling, frames-on-demand, optional Rust/numpy hot-loop later).

---

### WS2 — Agentic core: registry, run-context, event bus, blackboard 🟠

**Objective.** Make the "Agent Runtime & Orchestration Core" real (C4 §4) and adopt the
blackboard SSOT + event-bus reactions (C4 §10) instead of in-RAM state + request/reply.

**Scope / files:**
- `agents/base.py` — keep `Agent`/`Tool`/`RunContext` Protocols; add a concrete `RunContext`
  impl carrying `seed`, blackboard handle, and `emit(event)`.
- `agents/registry.py` — wire `AgentRegistry`/`ToolRegistry`; register Draw, Scheduler,
  Dispatcher, Progression, Aggregator, generators as `Agent`s with typed tools.
- `orchestrator/blackboard.py` — back it with the `Cache` port (Redis locally); versioned
  tournament state; `snapshot()` to the `StateStore`.
- `infra/ports.py` — add an `EventBus` port (`publish(topic, event)` / `subscribe(topic)`).
- `infra/redis_backend.py` — implement `EventBus` via Redis pub/sub; in-memory variant for tests.
- `orchestrator/fsm.py` — agents become **stateless functions over the blackboard**; the FSM
  reacts to `goal` / `matchday-complete` / `qualifier-decided` events rather than awaiting.

**Acceptance criteria.**
- Orchestrator resolves a full cup using only blackboard reads/writes + bus events (no shared
  mutable `Tournament` passed by reference).
- Killing the API mid-run and resuming from the last blackboard snapshot reproduces the
  identical remaining run (ties into WS5).
- Registry-driven dispatch: agents are looked up by name; tools declare `deterministic`.

**Tests.** `test_blackboard_roundtrip`, `test_eventbus_pubsub`, `test_orchestrator_via_bus`.

**Risks.** Determinism under event ordering (mitigate: per-round barriers + ordered event keys).

---

### WS3 — Tournament rules completeness 🟠

**Objective.** Encode the messy rules explicitly and test them (arch §14: "tiebreakers are
where tournaments get messy — unit-test them").

**Scope / files:**
- `ratings/standings.py` — full tiebreaker chain: points → GD → GF → **head-to-head**
  (mini-table among tied teams) → **fair-play** (cards from event logs) → seeded lot.
- `orchestrator/progression.py` — **third-place playoff** (SF losers) when `config.third_place`.
- `orchestrator/policy.py` — `TournamentPolicy.resolve_draw` becomes the single place knockout
  draws are decided (delegates to the engine's ET/penalty sub-procedure); `tiebreak(standings)`.
- `orchestrator/fsm.py` — add `Phase.THIRD_PLACE`; wire SF losers → playoff → bronze.
- `domain/tournament.py` — `Phase.THIRD_PLACE`; record bronze medallist.

**Acceptance criteria.**
- Three-way tie on points resolves deterministically and matches a hand-computed fixture.
- Fair-play tiebreak uses real card counts from the event log.
- A 32-team cup produces gold, silver, **and bronze**.

**Tests.** `test_tiebreakers` (incl. three-way + head-to-head + fair-play + seeded lot),
`test_third_place`, `test_resolve_draw_decisive`.

**Risks.** Head-to-head sub-grouping edge cases (mitigate: explicit fixtures in tests).

---

### WS4 — Live match viewing (frame streaming + HUD) 🟡

**Objective.** Make the live path work locally and surface the `match.html` UI in React,
fully in English.

**Scope / files:**
- `api/routes_stream.py` — a **WebSocket** `/ws/match/{id}` (local stand-in for Azure SignalR);
  `negotiate` returns the WS URL for local, SignalR token for `azure`.
- `infra/redis_backend.py` — frame fan-out via Redis pub/sub; the worker publishes frames as it
  simulates a `render`-flagged match.
- Frontend `realtime/ws.ts` — native WebSocket client feeding `simStore` (replaces the inert
  SignalR client locally).
- Frontend `components/match/CoachPanel.tsx` *(new)* — the HUD from `match.html`: score, clock,
  per-team **formation** and **tactical style** selectors (English), auto-coach toggle.
- Frontend `routes/...matches.$mid.tsx` — toggle **Live** vs **Replay**; reuse `PitchReplay`
  for both (live = streamed frames, replay = fetched frames).

**Acceptance criteria.**
- Opening a running match streams frames to the canvas in real time; pausing the worker pauses frames.
- Coach panel shows English formations/styles; changing them on a live exhibition match updates play.

**Tests.** `test_ws_frame_stream` (integration), Playwright smoke (optional).

**Risks.** WS lifecycle/back-pressure (mitigate: bounded ring buffer, drop-oldest).

---

### WS5 — Pause / resume & Run Supervisor 🟡

**Objective.** Implement real cooperative pause/resume (blueprint §5.8); API stops returning 501.

**Scope / files:**
- `orchestrator/supervisor.py` — `pause()` (stop consuming, snapshot state + event sequence),
  `resume()` (load snapshot, resume consuming — idempotent by `match_seed`).
- `api/routes_tournaments.py` — `/pause` and `/resume` drive the supervisor; status reflects `paused`.
- `domain/tournament.py` — `Phase.PAUSED` (or a `paused` flag + resume-phase).

**Acceptance criteria.** A cup paused mid-group-stage and resumed produces the **same** champion
and run-hash as an uninterrupted run with the same seed.

**Tests.** `test_pause_resume_determinism`.

---

### WS6 — Cloud parity, observability & CI gates 🟡

**Objective.** Make `WC_BACKEND=azure` real and enforce the architecture's CI gates (blueprint §6).

**Scope / files:**
- `infra/queue_servicebus.py` — implement `ServiceBusQueue` (send/receive/complete, dedup by seed).
- `infra/signalr.py` — implement `AzureSignalR` REST broadcast + `negotiate`.
- `observability/{metrics,tracing,run_hash}.py` — wire metrics/traces; expose `/metrics`;
  surface `winprob.win_prob` in a live "win probability" widget (closes the unused-`winprob` gap).
- `.github/workflows/ci.yml` *(new)* — run `pytest`, `ruff`, `mypy`; **gate on**
  `test_determinism` and `test_match_engine_golden`; build both Docker images.
- `scripts/check_english.py` *(new)* — fail on non-English tactical labels.

**Acceptance criteria.** CI is green and blocks merges on the determinism/golden gates; `azure`
backend smoke-tested against the emulators (or live, if creds present).

**Risks.** Service Bus emulator friction (mitigate: keep Redis as the supported local default;
Service Bus path covered by a guarded integration test).

---

## 4. Phasing & sequencing

```
Phase A (foundation)      Phase B (rules + agentic)     Phase C (experience)     Phase D (cloud)
WS1 Match Engine v2  ──▶  WS3 Tournament rules     ──▶  WS4 Live viewing     ──▶ WS6 Cloud parity
        │                 WS2 Agentic core (parallel)    WS5 Pause/resume          + CI gates
        └─ unblocks frames + decisive KO for WS3/WS4
```

- **WS1 is the critical path** (everything visual/decisive depends on it). Land it first.
- **WS2** can proceed in parallel with WS3 (different files).
- Each WS merges to `dev` via its own PR with green tests; `all-features` stays integration-stable.

**Indicative effort (engineering days):** WS1 ≈ 5–8 · WS2 ≈ 3–4 · WS3 ≈ 2–3 · WS4 ≈ 3 ·
WS5 ≈ 1–2 · WS6 ≈ 2–3. Total ≈ 16–23 days.

---

## 5. Cross-cutting guarantees

- **Determinism is sacred.** All randomness via `seed/provider.py` + `SeededRng`; ordered
  iteration only; LLM strictly off the hot path and cached by seed (arch §11, §14). Every WS
  ships with a determinism assertion.
- **Hexagonal discipline.** New capabilities (`EventBus`, `ReplayService`) are **ports**;
  adapters implement them; `domain`/`match_engine` stay dependency-free. Fixes gap #10.
- **English-only UI & code.** Enforced by `scripts/check_english.py` in CI.
- **Backward compatibility.** `WC_BACKEND=memory|local` keep working throughout; the engine swap
  is behind `MatchEngine.simulate`, so the orchestrator/API contracts are unchanged.

## 6. Definition of Done (whole effort)

1. Conformance review re-run shows **no 🔴/🟠** items outstanding.
2. `test_determinism` + `test_match_engine_golden` green in CI and gating merges.
3. A cup produces gold/silver/bronze; tiebreakers unit-tested incl. three-way ties.
4. Live and replay match views both animate the **real** engine's frames; coach panel in English.
5. Pause/resume reproduces an identical run; blackboard is the SSOT.
6. `WC_BACKEND=azure` path implemented and smoke-tested.
7. No Vietnamese strings in shipped code/UI.

---

## 7. Tracking

Work is tracked as one PR per workstream into `dev`:
`feat/ws1-engine-v2`, `feat/ws2-agentic-core`, `feat/ws3-rules`, `feat/ws4-live`,
`feat/ws5-pause-resume`, `feat/ws6-cloud-ci`. This document is updated as WSs land.

---

## 8. Progress log

### WS1 — Match Engine v2 · **in progress** (core landed)
- ✅ `tactics.py` (English formations + styles, `StyleDNA → style` resolver).
- ✅ `world.py` (Player/Ball/TeamState/World bodies, shots/possession counters).
- ✅ `physics.py` (arrive-steering, separation, ball roll, goal/out detection, **GK shot-stop + smother**).
- ✅ `behaviors.py` (carrier shoot/pass/dribble utilities, off-ball runs/overlap, marking, GK, kicks, offside).
- ✅ `runtime.py` (fixed-timestep loop, tackles/fouls/cards/send-off, dead-ball, penalties, coach loop,
  half-time switch, **extra time + shootout**, event + frame capture).
- ✅ `engine.py` `simulate(req, capture_frames=…)` — replaces the chance model.
- ✅ Replay endpoint re-runs the engine with frame capture (frames now match the score by construction);
  old choreographer `replay.py` deleted → **layering gap #10 closed** (api no longer needs the choreographer).
- ✅ Tests: `test_engine.py` (determinism, frame bounds, decisive KO, plausibility); e2e + suite green (8/8).
- ⏳ **Realism tuning (knob, not a blocker):** currently ~2.2 goals/team (target 1.3–1.6). Levers in play:
  GK reach, shot spread, `SHOOT_R`. Tracked for follow-up; deterministic + emergent behaviour is achieved.
- ⏳ Golden-master baseline record; headless perf budget assertion in CI.

**Perf:** ~0.6 s/match headless (≈0.6 s × 63 ≈ 40 s sequential; ~15–25 s in Docker with 4 workers).

### WS3 — Tournament rules · **done**
- ✅ Full tiebreaker chain in `ratings/standings.py`: points → GD → GF → **head-to-head**
  (mini-table among the tied cluster) → **fair-play** (disciplinary demerits) → seeded lot.
- ✅ Fair-play wired end-to-end: the engine emits demerits (`yellow=1`, `send-off=+3`) →
  `MatchStats`/`MatchSummary` → cumulative `Standing.fair`.
- ✅ **Third-place playoff** (SF losers) when `config.third_place`; `Phase.THIRD_PLACE`;
  tournament records gold / silver / **bronze** (`champion_id` / `runner_up_id` / `third_place_id`).
- ✅ `TournamentPolicy.resolve_draw` is now the single authority guaranteeing a decisive knockout
  (delegates to the engine's ET/shootout; seeded-lot safety net otherwise) — used by the FSM.
- ✅ API surfaces runner-up + bronze on the status DTO.
- ✅ Tests: `test_tiebreakers` (three-way head-to-head, fair-play, deterministic seeded lot),
  e2e `test_medals_gold_silver_bronze`; full suite green (12/12). Verified: a cup now yields
  gold/silver/bronze with a real third-place match.

### WS2 — Agentic core · **done** (pragmatic scope)
- ✅ **EventBus** port + Redis adapter (capped list per topic + pub/sub fan-out) and an in-memory
  adapter for tests; added to the `Deps` bundle.
- ✅ Concrete **`TournamentRunContext`** carrying the seed and a topic-scoped `emit()`.
- ✅ **AgentRegistry** populated and *used* by the orchestrator (sub-agents resolved by name).
- ✅ **Blackboard** backed by the `Cache` port writes a hot live status on every phase change
  (durable snapshots still go to Postgres via the supervisor) — the SSOT pattern.
- ✅ Orchestrator emits domain events (`run_started`, `phase`, `match`, `run_finished`) onto the bus;
  `GET /tournaments/{id}/activity` exposes the live agentic feed.
- ✅ Tests: `test_agentic` (bus history/scope, run-context emit, registry lookup) + e2e activity
  assertion; suite green (15/15).
- **Deliberate scope:** the FSM stays **await-based** (per-round barriers) for reproducibility;
  events are emitted for observability and to feed the live UI (WS4), rather than rewriting the
  conductor into a fully event-driven reactor. The bus/registry/blackboard substrate is now real.

### WS4–WS6 — not started.
