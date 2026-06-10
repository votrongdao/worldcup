# AI Agentic World Cup — Implementation Blueprint (React + TanStack · Python · Azure)

**Status:** Draft v1 · **Diagrams:** standard Mermaid (no `C4` syntax)

This document turns the architecture into a buildable blueprint:

1. Azure **solution architecture**
2. **Software architecture** (hexagonal / ports & adapters)
3. **Backend** (Python / FastAPI) — full file tree, module relationships, class diagrams, key skeletons
4. **Frontend** (React + TanStack) — full file tree, component hierarchy, data-flow, key skeletons
5. **All sequence diagrams** (end-to-end flows)

The deterministic **Match Engine** and the **one-AI-per-team Team Orchestrator** from the prior design are reused unchanged in intent; here they become Python packages.

---

## 1. Azure Solution Architecture

```mermaid
flowchart TB
  user["Operator / Analyst<br/>(Browser)"]
  fd["Azure Front Door + WAF<br/>(global entry, routing)"]

  subgraph edge["Frontend"]
    swa["Azure Static Web Apps<br/>React + TanStack (CDN)"]
  end

  subgraph aca["Azure Container Apps Environment"]
    api["orchestrator-api<br/>(FastAPI)"]
    workers["match-workers<br/>(KEDA-scaled consumers)"]
  end

  sb["Azure Service Bus<br/>(match dispatch queue)"]
  redis["Azure Cache for Redis<br/>(blackboard, pub/sub, hot state)"]
  pg["Azure DB for PostgreSQL<br/>(state + read models)"]
  blob["Azure Blob Storage<br/>(append-only event logs, replays)"]
  signalr["Azure SignalR Service<br/>(live match frames)"]
  aoai["Azure OpenAI<br/>(optional LLM gateway)"]
  kv["Azure Key Vault<br/>(secrets)"]
  acr["Azure Container Registry"]
  mon["Azure Monitor +<br/>Application Insights"]
  entra["Microsoft Entra ID<br/>(auth)"]

  user --> fd
  fd --> swa
  fd --> api
  swa -->|"REST (TanStack Query)"| api
  swa -->|"WebSocket frames"| signalr
  api -->|"enqueue match_seed"| sb
  sb -->|"scale trigger + messages"| workers
  workers -->|"append events"| blob
  workers -->|"push frames"| signalr
  workers --> redis
  api --> redis
  api --> pg
  workers --> pg
  api -.->|"commentary (cached)"| aoai
  api --> kv
  workers --> kv
  acr -.->|"images"| aca
  api --> mon
  workers --> mon
  swa -.->|"login"| entra
  api -.->|"validate token"| entra
```

### 1.1 Service responsibility map

| Azure service | Role | Notes |
|---|---|---|
| **Static Web Apps** | Host the React + TanStack SPA | Global CDN, free SSL, GitHub Actions deploy |
| **Front Door + WAF** | Single global entry, route `/` → SWA, `/api` → API | TLS, WAF, caching |
| **Container Apps – orchestrator-api** | FastAPI: tournament lifecycle, queries, SignalR negotiate | Min 1 replica; HTTP ingress |
| **Container Apps – match-workers** | Consume queue, run Match Engine, emit events/frames | KEDA scale-to-zero on Service Bus depth |
| **Service Bus** | Match dispatch queue (one message per fixture) | Sessions/dedup by `match_seed` |
| **Cache for Redis** | Blackboard, pub/sub for live frames, hot tournament state | |
| **PostgreSQL Flexible Server** | Persisted state + read models (standings, bracket) | SQLAlchemy + Alembic |
| **Blob Storage** | Append-only event logs & replays | Immutable containers; cheap |
| **SignalR Service** | Push live match frames to browsers | Serverless mode behind FastAPI negotiate |
| **Azure OpenAI** | Optional names/commentary/slow-loop hints | Behind LLM Gateway, seed-keyed cache |
| **Key Vault / Managed Identity** | Secrets & connection strings | No secrets in env |
| **Container Registry** | Images for both Container Apps | |
| **Monitor + App Insights** | Metrics, traces, logs, run-hash verifier | |
| **Entra ID** | Operator auth | Optional for public demos |

---

## 2. Software Architecture (Hexagonal / Ports & Adapters)

```mermaid
flowchart TB
  subgraph driving["Driving side (entry)"]
    apilayer["API (FastAPI routes)"]
    workerlayer["Worker entrypoint"]
  end

  subgraph app["Application (use cases)"]
    orch["orchestrator (FSM, draw, scheduler,<br/>dispatcher, progression, supervisor)"]
    gen["generation"]
    ratings["ratings"]
    agents["agents (Agent, Tool, RunContext)"]
  end

  subgraph core["Domain core (pure, deterministic)"]
    domain["domain models + seed + match_engine"]
  end

  subgraph ports["Ports (interfaces)"]
    p["MatchQueue · StateStore · EventLog ·<br/>Cache · SignalRPort · LlmGateway"]
  end

  subgraph adapters["Driven adapters (Azure)"]
    a["ServiceBus · Postgres · Blob ·<br/>Redis · SignalR · Azure OpenAI"]
  end

  apilayer --> app
  workerlayer --> app
  app --> core
  app --> ports
  adapters -.implements.-> ports
  app -.depends only on.-> ports
```

**Dependency rule:** arrows point inward. `domain` + `match_engine` depend on nothing external; `application` depends on `domain` and `ports`; Azure `adapters` implement `ports`. This keeps the deterministic core testable and swappable (e.g., Postgres → Cosmos with no domain change).

---

## 3. Backend — Python (FastAPI)

### 3.1 Full file tree

```text
backend/
├─ pyproject.toml                  # deps: fastapi, pydantic, sqlalchemy, alembic,
│                                  #   azure-servicebus, azure-storage-blob, redis,
│                                  #   azure-identity, openai, uvicorn, pytest
├─ Dockerfile                      # multi-stage; one image, two commands (api|worker)
├─ alembic.ini
├─ azure/
│  ├─ main.bicep                   # resource group composition
│  ├─ containerapps.bicep          # api + workers + env + KEDA rules
│  └─ data.bicep                   # postgres, redis, servicebus, blob, signalr
├─ src/
│  ├─ app/
│  │  ├─ main.py                   # FastAPI factory, router mount, middleware, lifespan
│  │  ├─ config.py                 # Settings (pydantic-settings), Azure bindings
│  │  ├─ deps.py                   # DI providers (ports → adapters via Settings)
│  │  └─ logging.py                # structured logging → App Insights
│  ├─ api/
│  │  ├─ routes_tournaments.py     # POST /tournaments, GET /{id}, /pause, /resume
│  │  ├─ routes_matches.py         # GET /matches/{id}, /events, /replay
│  │  ├─ routes_teams.py           # GET /teams/{id}, /players
│  │  ├─ routes_stream.py          # POST /negotiate (SignalR), WS fallback
│  │  └─ schemas.py                # API request/response DTOs (Pydantic)
│  ├─ domain/                      # PURE — no I/O, no Azure
│  │  ├─ ids.py                    # typed IDs
│  │  ├─ player.py                 # Player, Role
│  │  ├─ team.py                   # Team, CoachProfile, StyleDNA, Formation
│  │  ├─ tournament.py             # Tournament, Phase, Fixture, Standing, Config
│  │  ├─ match.py                  # MatchRequest, MatchRules, MatchResult, MatchEvent
│  │  └─ events.py                 # DomainEvent taxonomy
│  ├─ seed/
│  │  ├─ provider.py               # sub_seed(master, *path) — stable hashing
│  │  └─ rng.py                    # SeededRng (LCG) — parity with JS engine
│  ├─ generation/
│  │  ├─ national_team_generator.py
│  │  ├─ identity.py               # tier + styleDNA
│  │  ├─ player_generator.py
│  │  ├─ coach_generator.py
│  │  └─ team_builder.py           # XI, validation, rating
│  ├─ match_engine/               # the reused simulation (deterministic)
│  │  ├─ engine.py                 # MatchEngine.simulate(req) → MatchResult
│  │  ├─ runtime.py                # fixed-timestep accumulator loop
│  │  ├─ physics.py                # kinematics, collisions, ball
│  │  ├─ world.py                  # MatchWorldState
│  │  ├─ team_orchestrator.py      # coach (slow) + orchestrate (fast)
│  │  ├─ behaviors.py              # role → action (pass/shoot/dribble/clear)
│  │  ├─ recorder.py               # MatchEvent recorder + frame sink
│  │  └─ policies/
│  │     ├─ base.py                # DecisionPolicy (interface)
│  │     ├─ heuristic.py           # HeuristicPolicy (default)
│  │     └─ rl.py                  # RLPolicy (pluggable stub)
│  ├─ orchestrator/
│  │  ├─ fsm.py                    # TournamentOrchestrator lifecycle FSM
│  │  ├─ draw.py                   # DrawAgent
│  │  ├─ scheduler.py              # SchedulerAgent
│  │  ├─ dispatcher.py             # MatchDispatcher → MatchQueue port
│  │  ├─ progression.py            # qualifiers, bracket build, advancement
│  │  ├─ aggregator.py             # ResultAggregator (+ optional commentary)
│  │  ├─ policy.py                 # TournamentPolicy (format, tiebreakers, ET/pens)
│  │  ├─ supervisor.py             # RunSupervisor (snapshot/resume)
│  │  └─ blackboard.py             # Blackboard (Cache port)
│  ├─ ratings/
│  │  ├─ elo.py                    # rating update
│  │  ├─ standings.py              # table calc + tiebreaker chain
│  │  └─ winprob.py
│  ├─ agents/
│  │  ├─ base.py                   # Agent, Tool, RunContext (Protocols)
│  │  └─ registry.py               # AgentRegistry, ToolRegistry
│  ├─ workers/
│  │  ├─ match_worker.py           # consume queue → simulate → events/frames
│  │  └─ main.py                   # worker process entrypoint
│  ├─ infra/                       # DRIVEN ADAPTERS (Azure)
│  │  ├─ ports.py                  # Protocols: MatchQueue, StateStore, EventLog,
│  │  │                            #   Cache, SignalRPort, LlmGateway
│  │  ├─ queue_servicebus.py
│  │  ├─ store_postgres.py         # SQLAlchemy models + repositories
│  │  ├─ eventlog_blob.py
│  │  ├─ cache_redis.py
│  │  ├─ signalr.py
│  │  └─ llm_gateway.py            # Azure OpenAI + seed-keyed cache
│  └─ observability/
│     ├─ metrics.py
│     ├─ tracing.py
│     └─ run_hash.py               # hash of ordered event log
└─ tests/
   ├─ test_determinism.py          # same seed → same run hash
   ├─ test_tiebreakers.py          # incl. three-way ties
   ├─ test_match_engine_golden.py  # golden-master event log
   └─ test_generation.py
```

### 3.2 Module dependency graph (allowed directions)

```mermaid
flowchart LR
  api["api"] --> orchestrator["orchestrator"]
  api --> ratings["ratings"]
  api --> infra["infra (adapters)"]
  workers["workers"] --> match_engine["match_engine"]
  workers --> infra
  orchestrator --> domain["domain"]
  orchestrator --> agents["agents"]
  orchestrator --> ports["infra.ports"]
  generation["generation"] --> domain
  generation --> seed["seed"]
  match_engine --> domain
  match_engine --> seed
  ratings --> domain
  agents --> domain
  infra -.implements.-> ports
  domain --> nothing["(no external deps)"]
```

### 3.3 Class diagram — Domain model

```mermaid
classDiagram
  class Tournament {
    +str id
    +TournamentConfig config
    +Phase phase
    +str run_hash
  }
  class TournamentConfig {
    +str format
    +int teams
    +int groups
    +int per_group
    +int advance_per_group
    +bool third_place
    +int seed
  }
  class Team {
    +str id
    +str nation
    +int tier
    +StyleDNA style_dna
    +float rating
  }
  class Player {
    +str id
    +Role role
    +float pace
    +float shooting
    +float passing
    +float defending
    +float stamina
  }
  class CoachProfile {
    +Formation formation
    +float aggression
    +float line_height
    +float tempo
    +float pressing
  }
  class Fixture {
    +str id
    +Phase phase
    +str home_id
    +str away_id
  }
  class Standing {
    +str team_id
    +int played
    +int pts
    +int gf
    +int ga
  }
  class MatchResult {
    +int score_home
    +int score_away
    +str decided_by
    +str winner
  }
  class MatchEvent {
    +float t
    +str type
    +str team
  }

  Tournament *-- TournamentConfig
  Tournament o-- Team
  Tournament o-- Fixture
  Tournament o-- Standing
  Team *-- Player
  Team *-- CoachProfile
  Fixture --> MatchResult
  MatchResult *-- MatchEvent
```

### 3.4 Class diagram — Match Engine & decision policies

```mermaid
classDiagram
  class MatchEngine {
    +simulate(req) MatchResult
  }
  class SimulationRuntime {
    +run(world, rules) MatchResult
    +step(dt) void
  }
  class PhysicsEngine {
    +integrate(world, dt) void
    +resolve_collisions(world) void
  }
  class MatchWorldState {
    +players list
    +ball Ball
    +score tuple
  }
  class TeamOrchestrator {
    +coach_plan(slow) Plan
    +orchestrate(tick) Commands
  }
  class DecisionPolicy {
    <<interface>>
    +allocate_roles(state, plan) RoleMap
    +resolve_action(player, state) Action
  }
  class HeuristicPolicy
  class RLPolicy
  class EventRecorder {
    +record(event) void
    +log() list
  }

  MatchEngine ..> SimulationRuntime
  SimulationRuntime ..> PhysicsEngine
  SimulationRuntime ..> TeamOrchestrator
  SimulationRuntime o-- MatchWorldState
  SimulationRuntime ..> EventRecorder
  TeamOrchestrator o-- DecisionPolicy
  DecisionPolicy <|.. HeuristicPolicy
  DecisionPolicy <|.. RLPolicy
```

### 3.5 Class diagram — Orchestrator & agent framework

```mermaid
classDiagram
  class Agent {
    <<interface>>
    +str name
    +run(input, ctx) Any
  }
  class Tool {
    <<interface>>
    +str name
    +bool deterministic
    +invoke(input, ctx) Any
  }
  class RunContext {
    +int seed
    +emit(event) void
  }
  class Blackboard {
    +get(key) Any
    +set(key, value) void
    +snapshot() State
  }
  class TournamentOrchestrator {
    +Phase phase
    +start(config) void
    +advance() void
  }
  class DrawAgent
  class SchedulerAgent
  class MatchDispatcher {
    +dispatch(fixtures) void
  }
  class ProgressionManager {
    +qualifiers(group) list
    +build_bracket() list
  }
  class ResultAggregator
  class TournamentPolicy {
    +tiebreak(standings) list
    +resolve_draw(match) MatchResult
  }
  class RunSupervisor {
    +snapshot() void
    +resume() void
  }

  Agent <|.. DrawAgent
  Agent <|.. SchedulerAgent
  Agent <|.. ResultAggregator
  TournamentOrchestrator o-- DrawAgent
  TournamentOrchestrator o-- SchedulerAgent
  TournamentOrchestrator o-- MatchDispatcher
  TournamentOrchestrator o-- ProgressionManager
  TournamentOrchestrator o-- ResultAggregator
  TournamentOrchestrator o-- TournamentPolicy
  TournamentOrchestrator o-- RunSupervisor
  RunContext o-- Blackboard
  Agent ..> RunContext
  Tool ..> RunContext
```

### 3.6 Class diagram — Ports & Azure adapters

```mermaid
classDiagram
  class MatchQueue {
    <<interface>>
    +enqueue(req) void
    +consume() MatchRequest
  }
  class StateStore {
    <<interface>>
    +save(tournament) void
    +load(id) Tournament
  }
  class EventLog {
    <<interface>>
    +append(events) void
    +read(match_id) list
  }
  class Cache {
    <<interface>>
    +get(key) Any
    +set(key, value) void
  }
  class SignalRPort {
    <<interface>>
    +push(group, frame) void
  }
  class LlmGateway {
    <<interface>>
    +complete(prompt, seed_key) str
  }

  class ServiceBusQueue
  class PostgresStore
  class BlobEventLog
  class RedisCache
  class AzureSignalR
  class AzureOpenAIGateway

  MatchQueue <|.. ServiceBusQueue
  StateStore <|.. PostgresStore
  EventLog <|.. BlobEventLog
  Cache <|.. RedisCache
  SignalRPort <|.. AzureSignalR
  LlmGateway <|.. AzureOpenAIGateway
```

### 3.7 Representative skeletons

```python
# src/agents/base.py
from typing import Protocol, Any, runtime_checkable

@runtime_checkable
class RunContext(Protocol):
    seed: int
    def emit(self, event: "DomainEvent") -> None: ...

class Tool(Protocol):
    name: str
    deterministic: bool
    def invoke(self, input: Any, ctx: RunContext) -> Any: ...

class Agent(Protocol):
    name: str
    async def run(self, input: Any, ctx: RunContext) -> Any: ...
```

```python
# src/match_engine/policies/base.py
from typing import Protocol
from src.domain.match import Action
from src.match_engine.world import MatchWorldState

class DecisionPolicy(Protocol):
    def allocate_roles(self, state: MatchWorldState, plan: "Plan") -> "RoleMap": ...
    def resolve_action(self, player_id: str, state: MatchWorldState) -> Action: ...
```

```python
# src/match_engine/engine.py
from src.domain.match import MatchRequest, MatchResult
from src.match_engine.runtime import SimulationRuntime

class MatchEngine:
    def __init__(self, runtime: SimulationRuntime) -> None:
        self._runtime = runtime

    def simulate(self, req: MatchRequest) -> MatchResult:
        # pure function of (home, away, seed, rules) — fully deterministic
        return self._runtime.run(req)
```

```python
# src/orchestrator/fsm.py  (abridged)
from src.domain.tournament import Phase, TournamentConfig
from src.infra.ports import MatchQueue, StateStore, EventLog

class TournamentOrchestrator:
    def __init__(self, queue: MatchQueue, store: StateStore, log: EventLog, deps): ...

    async def start(self, config: TournamentConfig) -> None:
        self.phase = Phase.GENERATING
        await self._generate_teams(config)
        self.phase = Phase.DRAW
        await self._draw_groups()
        await self._run_group_stage()      # dispatch matchdays in parallel
        await self._run_knockouts()        # r16 → qf → sf → final (ET/pens)
        self.phase = Phase.DONE
```

```python
# src/workers/match_worker.py  (abridged)
async def handle(message, engine, log: EventLog, signalr):
    req = MatchRequest.parse_raw(message.body)
    result = engine.simulate(req)                 # deterministic
    await log.append(result.events)               # Blob append-only
    await signalr.push(req.match_id, result.frames_summary)
    return result
```

```python
# src/app/deps.py  (ports → Azure adapters, chosen by Settings)
def build_queue(settings) -> MatchQueue:
    return ServiceBusQueue(settings.servicebus_conn)
def build_store(settings) -> StateStore:
    return PostgresStore(settings.pg_dsn)
def build_eventlog(settings) -> EventLog:
    return BlobEventLog(settings.blob_conn)
```

---

## 4. Frontend — React + TanStack

Stack: **Vite + React + TypeScript**, **TanStack Query** (server state), **TanStack Router** (routing), **TanStack Table** (standings/squad), **@microsoft/signalr** (live frames), Canvas2D viewer.

### 4.1 Full file tree

```text
frontend/
├─ package.json                   # react, @tanstack/react-query, @tanstack/react-router,
│                                  #   @tanstack/react-table, @microsoft/signalr, vite
├─ vite.config.ts
├─ tsconfig.json
├─ index.html
├─ staticwebapp.config.json       # Azure Static Web Apps routing/auth
└─ src/
   ├─ main.tsx                     # bootstrap: QueryClientProvider + RouterProvider
   ├─ app/
   │  ├─ providers.tsx             # Query + Router + SignalR + Theme providers
   │  └─ queryClient.ts            # TanStack Query client (staleTime, retry)
   ├─ router.tsx                   # route tree assembly
   ├─ routes/                      # TanStack Router routes
   │  ├─ __root.tsx                # AppShell + nav
   │  ├─ index.tsx                 # Dashboard: create/start tournament
   │  ├─ tournaments.$id.tsx       # overview (phase stepper, summary)
   │  ├─ tournaments.$id.groups.tsx
   │  ├─ tournaments.$id.bracket.tsx
   │  ├─ matches.$id.tsx           # live match
   │  ├─ matches.$id.replay.tsx    # replay
   │  └─ teams.$id.tsx             # squad + coach
   ├─ api/
   │  ├─ client.ts                 # fetch wrapper (baseURL, auth header)
   │  ├─ tournaments.ts            # createTournament, getStatus, pause, resume
   │  ├─ matches.ts                # getMatch, getEvents
   │  ├─ teams.ts                  # getTeam
   │  └─ types.ts                  # API types mirroring backend Pydantic DTOs
   ├─ hooks/                       # TanStack Query hooks
   │  ├─ useCreateTournament.ts    # useMutation
   │  ├─ useTournament.ts          # useQuery (polled while running)
   │  ├─ useStandings.ts
   │  ├─ useBracket.ts
   │  ├─ useMatch.ts
   │  ├─ useMatchEvents.ts         # replay source
   │  └─ useLiveMatch.ts           # SignalR subscription → frame buffer
   ├─ stores/
   │  ├─ uiStore.ts                # selected entities, theme (TanStack Store/Zustand)
   │  └─ simStore.ts               # live frame ring buffer
   ├─ components/
   │  ├─ layout/{AppShell,NavBar}.tsx
   │  ├─ tournament/
   │  │  ├─ PhaseStepper.tsx
   │  │  ├─ GroupTable.tsx         # TanStack Table
   │  │  ├─ BracketView.tsx
   │  │  └─ FixtureList.tsx
   │  ├─ match/
   │  │  ├─ PitchCanvas.tsx        # Canvas2D renderer (live + replay)
   │  │  ├─ MatchScoreboard.tsx
   │  │  ├─ MatchTimeline.tsx
   │  │  └─ ReplayControls.tsx
   │  ├─ team/{SquadTable,CoachCard,PlayerRadar}.tsx
   │  └─ common/{DataTable,Loading,ErrorState}.tsx
   ├─ canvas/
   │  ├─ renderer.ts               # draw pitch/players/ball from a Frame
   │  ├─ interpolate.ts            # smooth between frames
   │  └─ types.ts                  # Frame, RenderState
   ├─ realtime/
   │  └─ signalr.ts                # connection lifecycle, negotiate via API
   ├─ lib/{format.ts,seed.ts}
   └─ styles/theme.css
```

### 4.2 Component hierarchy

```mermaid
flowchart TB
  main["main.tsx"] --> providers["Providers<br/>(Query + Router + SignalR)"]
  providers --> root["__root (AppShell + NavBar)"]
  root --> dash["Dashboard (index)"]
  root --> tour["Tournament Overview"]
  root --> match["Live Match"]
  root --> replay["Replay"]
  root --> team["Team"]
  tour --> stepper["PhaseStepper"]
  tour --> groups["GroupTable (TanStack Table)"]
  tour --> bracket["BracketView"]
  tour --> fixtures["FixtureList"]
  match --> canvas["PitchCanvas"]
  match --> score["MatchScoreboard"]
  match --> timeline["MatchTimeline"]
  replay --> canvas2["PitchCanvas"]
  replay --> controls["ReplayControls"]
  team --> squad["SquadTable (TanStack Table)"]
  team --> coach["CoachCard"]
  team --> radar["PlayerRadar"]
```

### 4.3 Frontend data flow (TanStack Query + SignalR)

```mermaid
flowchart LR
  comp["Components"] --> hooks["TanStack Query hooks"]
  hooks --> qc["QueryClient (cache)"]
  qc --> client["api/client.ts (fetch)"]
  client --> api["FastAPI /api"]
  mut["useMutation (create/pause)"] --> client
  mut -.invalidate.-> qc

  api --> negotiate["/negotiate → SignalR token"]
  negotiate --> sr["SignalR connection"]
  sr --> simstore["simStore (frame buffer)"]
  simstore --> canvas["PitchCanvas"]
  canvas --> renderer["canvas/renderer.ts"]
```

### 4.4 Representative skeletons

```tsx
// src/app/queryClient.ts
import { QueryClient } from "@tanstack/react-query";
export const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 5_000, retry: 2 } },
});
```

```tsx
// src/hooks/useTournament.ts
import { useQuery } from "@tanstack/react-query";
import { getStatus } from "../api/tournaments";
export function useTournament(id: string) {
  return useQuery({
    queryKey: ["tournament", id],
    queryFn: () => getStatus(id),
    refetchInterval: (q) => (q.state.data?.phase === "done" ? false : 2000),
  });
}
```

```tsx
// src/hooks/useLiveMatch.ts
import { useEffect } from "react";
import { connectMatch } from "../realtime/signalr";
import { useSimStore } from "../stores/simStore";
export function useLiveMatch(matchId: string) {
  const push = useSimStore((s) => s.pushFrame);
  useEffect(() => {
    const conn = connectMatch(matchId, push);
    return () => { conn.stop(); };
  }, [matchId, push]);
}
```

```tsx
// src/components/match/PitchCanvas.tsx  (abridged)
import { useRef, useEffect } from "react";
import { drawFrame } from "../../canvas/renderer";
import { useSimStore } from "../../stores/simStore";
export function PitchCanvas() {
  const ref = useRef<HTMLCanvasElement>(null);
  const frames = useSimStore((s) => s.frames);
  useEffect(() => {
    const ctx = ref.current!.getContext("2d")!;
    let raf = requestAnimationFrame(function loop() {
      drawFrame(ctx, frames.current());     // interpolated frame
      raf = requestAnimationFrame(loop);
    });
    return () => cancelAnimationFrame(raf);
  }, [frames]);
  return <canvas ref={ref} className="pitch" />;
}
```

```ts
// src/api/client.ts
const BASE = import.meta.env.VITE_API_BASE ?? "/api";
export async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" }, ...init,
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json() as Promise<T>;
}
```

---

## 5. Sequence Diagrams (all flows)

### 5.1 Create & start a tournament

```mermaid
sequenceDiagram
  actor Op as Operator (Browser)
  participant FE as React + TanStack
  participant API as FastAPI
  participant TO as Tournament Orchestrator
  participant GEN as Generation Service
  participant ST as Postgres State
  Op->>FE: fill config, click Start
  FE->>API: POST /tournaments (config, seed)
  API->>TO: start(config)
  TO->>GEN: generate N teams
  GEN-->>TO: validated teams
  TO->>ST: persist teams + tournament
  API-->>FE: 202 Accepted (tournament id)
  FE->>FE: useTournament(id) begins polling
```

### 5.2 Team generation (deterministic)

```mermaid
sequenceDiagram
  participant TO as Orchestrator
  participant NTG as National Team Generator
  participant SEED as Seed Provider
  participant PG as Player Generator
  participant CG as Coach Generator
  participant TB as Team Builder
  loop for each nation i
    TO->>NTG: generate nation i
    NTG->>SEED: sub_seed(master, nation, i)
    NTG->>PG: squad from tier and DNA
    PG-->>NTG: squad
    NTG->>CG: coach from DNA
    CG-->>NTG: coach profile
    NTG->>TB: build XI, validate, rate
    TB-->>NTG: validated team
  end
```

### 5.3 Group matchday (parallel via Service Bus + workers)

```mermaid
sequenceDiagram
  participant TO as Orchestrator
  participant DSP as Match Dispatcher
  participant SB as Service Bus
  participant W as Match Worker (scaled)
  participant ME as Match Engine
  participant BLOB as Blob Event Log
  participant RT as Ratings Engine
  TO->>DSP: dispatch matchday fixtures
  par one message per fixture
    DSP->>SB: enqueue match_seed
    SB->>W: deliver (KEDA scales workers)
    W->>ME: simulate(req)
    ME-->>W: result + events
    W->>BLOB: append events
    W-->>DSP: result
  end
  DSP-->>TO: matchday results
  TO->>RT: recompute standings + ratings
```

### 5.4 Single match simulation (inside a worker)

```mermaid
sequenceDiagram
  participant W as Match Worker
  participant ME as Match Engine
  participant RT as Simulation Runtime
  participant TA as Team Orchestrator A
  participant TB as Team Orchestrator B
  participant PH as Physics Engine
  participant REC as Event Recorder
  W->>ME: simulate(req)
  ME->>RT: run(world, rules)
  loop each tick
    RT->>TA: perceive + decide
    RT->>TB: perceive + decide
    TA-->>PH: player commands
    TB-->>PH: player commands
    RT->>PH: step(dt) x substeps
    PH-->>RT: world updated
    RT->>REC: record events
  end
  RT-->>ME: MatchResult + events
  ME-->>W: MatchResult
```

### 5.5 Live match viewing (SignalR)

```mermaid
sequenceDiagram
  actor An as Analyst (Browser)
  participant FE as React
  participant API as FastAPI
  participant SR as Azure SignalR
  participant W as Match Worker
  An->>FE: open live match M
  FE->>API: POST /negotiate (match M)
  API-->>FE: SignalR url + token
  FE->>SR: connect, join group M
  W->>SR: push frame summaries for M
  SR-->>FE: frames
  FE->>FE: simStore buffers → PitchCanvas renders
```

### 5.6 Replay from event log

```mermaid
sequenceDiagram
  actor An as Analyst
  participant FE as React
  participant API as FastAPI
  participant BLOB as Blob Event Log
  An->>FE: open replay for match M
  FE->>API: GET /matches/M/events
  API->>BLOB: read event log M
  BLOB-->>API: ordered events
  API-->>FE: events
  FE->>FE: deterministically re-render via canvas
```

### 5.7 Knockout resolution (ET / penalties)

```mermaid
sequenceDiagram
  participant TO as Orchestrator
  participant ME as Match Engine
  participant POL as Tournament Policy
  TO->>ME: simulate(knockout req)
  ME-->>TO: result (maybe drawn)
  alt drawn and ET enabled
    TO->>ME: simulate extra time
    ME-->>TO: result
  end
  alt still drawn
    TO->>POL: resolve via penalties (seeded)
    POL-->>TO: decisive winner
  end
  TO->>TO: advance winner in bracket
```

### 5.8 Pause & resume (Run Supervisor)

```mermaid
sequenceDiagram
  actor Op as Operator
  participant API as FastAPI
  participant SUP as Run Supervisor
  participant ST as Postgres
  participant SB as Service Bus
  Op->>API: POST /tournaments/id/pause
  API->>SUP: pause()
  SUP->>SB: stop consuming
  SUP->>ST: snapshot state + event seq
  Op->>API: POST /tournaments/id/resume
  API->>SUP: resume()
  SUP->>ST: load last snapshot
  SUP->>SB: resume consuming (idempotent by seed)
```

### 5.9 Standings / bracket query (read model)

```mermaid
sequenceDiagram
  participant FE as React + TanStack Query
  participant API as FastAPI
  participant ST as Postgres read model
  FE->>API: GET /tournaments/id/standings
  API->>ST: select standings projection
  ST-->>API: rows
  API-->>FE: standings
  FE->>FE: GroupTable (TanStack Table) renders
```

### 5.10 Optional LLM commentary (cached)

```mermaid
sequenceDiagram
  participant AGG as Result Aggregator
  participant GW as LLM Gateway
  participant CACHE as Redis cache
  participant AOAI as Azure OpenAI
  AGG->>GW: narrate(match, seed_key)
  GW->>CACHE: get(seed_key)
  alt cache hit
    CACHE-->>GW: cached text
  else miss
    GW->>AOAI: completion(prompt)
    AOAI-->>GW: text
    GW->>CACHE: set(seed_key, text)
  end
  GW-->>AGG: commentary
```

---

## 6. Build & Deploy Notes

- **One backend image, two commands.** `uvicorn src.app.main:app` for the API; `python -m src.workers.main` for workers. Same image → same Match Engine code on both paths (golden-master tested).
- **Frontend** builds to static assets → Azure Static Web Apps; `VITE_API_BASE` points at Front Door `/api`.
- **Infra as code** in `azure/*.bicep`; secrets via Key Vault + Managed Identity (no connection strings in env).
- **CI gates:** `test_determinism` asserts run-hash stability; `test_match_engine_golden` compares worker output to the recorded baseline; both must pass before deploy.
- **Scaling:** workers scale-to-zero and scale-out on Service Bus depth (KEDA); the API stays at ≥1 replica for SignalR negotiate and queries.
