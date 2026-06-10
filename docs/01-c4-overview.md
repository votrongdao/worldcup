# AI Agentic World Cup Orchestration Framework — C4 Architecture

> A hierarchical multi-agent framework that **generates national teams**, **builds them**, and **autonomously runs an entire World Cup end-to-end** — from team generation and the group draw, through the group stage and knockout rounds, to the final and the crowning of a champion.
>
> This document uses the **C4 model** (Context → Container → Component → Dynamic) expressed in **standard Mermaid** (flowchart, state, sequence, ER). It builds directly on the match-level *one-AI-per-team orchestrator* designed previously — that design now becomes the **Match Engine Service** at the bottom of this hierarchy.

---

## 1. Goals & Non-Goals

**Goals**
- Generate `N` distinct national teams (rosters, coaches, tactical identities) deterministically from a seed.
- Run a complete tournament lifecycle without human intervention: draw → groups → knockouts → final.
- Reuse the existing physics-based match simulation as a headless, batch-runnable service.
- Be **agentic**: pluggable policy agents, a shared blackboard, an event bus, and a top-level conductor that plans and dispatches.
- Be **reproducible**: the same seed always yields the same tournament.

**Non-Goals**
- Putting an LLM inside the per-tick physics loop (latency + non-determinism). LLMs stay strictly **off the hot path**.
- Real player/nation licensing or real-world data. Everything is generated.
- Real-time multiplayer or betting features.

---

## 2. Design Principles

1. **Hierarchical orchestration.** Three orchestration scales: *Tournament* (whole cup) → *Match* (one game) → *Team* (11 players + coach). Each higher level treats the lower level as a tool/service.
2. **Deterministic core, optional creative edge.** A seeded RNG drives all generation and simulation. LLMs only add *flavor* (names, style narratives, commentary) and *slow-loop tactical hints* — always cacheable by seed.
3. **Agents own decisions; engines own mechanics.** Agents decide *what* (draw, dispatch, allocate roles, advance teams). Deterministic engines compute *how* (physics, standings math, Elo).
4. **Stateless agents over a shared blackboard.** Agents read/write a versioned tournament state; nothing critical lives only in an agent's head, enabling replay and parallelism.
5. **Parallelize the independent.** Matches within the same round are independent and run concurrently across Match Engine workers.

---

## 3. C4 Level 1 — System Context

```mermaid
flowchart LR
  operator["Operator / Organizer<br/>[Person]<br/>configures the cup: team count,<br/>seed, format; starts & watches"]
  analyst["Analyst / Spectator<br/>[Person]<br/>consumes live view, results,<br/>replays, narratives"]
  sys["AI Agentic World Cup<br/>Orchestration Framework<br/>[Software System]<br/>generates teams and autonomously<br/>runs a full World Cup end to end"]
  llm["LLM Inference Service<br/>[External, optional]<br/>names, style text, commentary,<br/>slow-loop tactical hints"]
  store["Results & Replay Store<br/>[External]<br/>events, standings, brackets, replays"]

  operator -->|"configure & start tournament"| sys
  sys -->|"live view, results, narrative"| analyst
  sys -.->|"flavor & commentary (off hot path)"| llm
  sys -->|"persist events, standings, replays"| store
```

The framework is a single deployable system. Humans only configure and observe. The two external dependencies are optional (LLM) or supporting (persistence) — the core can run fully self-contained and deterministic without either.

---

## 4. C4 Level 2 — Containers

```mermaid
flowchart TB
  operator["Operator [Person]"]
  analyst["Analyst / Spectator [Person]"]
  llm["LLM Inference Service [External]"]
  store["Results & Replay Store [External]"]

  subgraph SYS["AI Agentic World Cup Orchestration Framework"]
    runtime["Agent Runtime & Orchestration Core<br/>[Container]<br/>agent registry, tool dispatch,<br/>event bus, blackboard, memory"]
    tour["Tournament Orchestrator Service<br/>[Container: stateful planner]<br/>draw, schedule, progression, final"]
    gen["Generation Service<br/>[Container: generator agents]<br/>nations, players, coaches, team build"]
    match["Match Engine Service<br/>[Container: headless + rendered]<br/>runs ONE match via 2 Team<br/>Orchestrators + physics"]
    ratings["Analytics & Ratings Engine<br/>[Container]<br/>Elo/strength, win-prob, projections"]
    tstate["Tournament State Store<br/>[Container: in-memory + persisted]<br/>groups, standings, bracket, fixtures"]
    viewer["Viewer / Replay Front-end<br/>[Container: Canvas2D]<br/>light, text-free top-down view"]
    gw["LLM Gateway<br/>[Container]<br/>routing, caching, guardrails"]
  end

  operator -->|"start / configure"| tour
  tour -->|"request team generation"| gen
  gen -->|"validated teams"| tstate
  tour -->|"dispatch matches"| match
  match -->|"result + events"| tour
  match -->|"read team data"| tstate
  tour -->|"update standings / bracket"| tstate
  tour -->|"progression & tiebreaks"| ratings
  ratings -->|"reads results"| tstate
  match -->|"stream frames"| viewer
  analyst -->|"watch / replay"| viewer
  tour -->|"persist"| store
  match -->|"persist events"| store
  gen -.->|"names / style"| gw
  tour -.->|"commentary"| gw
  gw -.-> llm

  tour -.->|"runs on"| runtime
  gen -.->|"runs on"| runtime
  match -.->|"runs on"| runtime
```

### Container responsibilities

| Container | Responsibility | Notes |
|---|---|---|
| **Agent Runtime & Orchestration Core** | The agentic substrate: registers agents, dispatches their tools, routes events, hosts the shared blackboard and memory. | This is the "framework." Maps well to a LangGraph-style state graph + a worker pool. |
| **Tournament Orchestrator** | Top-level conductor. A state machine over the cup lifecycle; owns draw, scheduling, progression, bracket, and the final. | Stateful but persists everything to the State Store for replay. |
| **Generation Service** | Hosts the generator agents that produce nations, players, coaches, and assembled teams. | Fully deterministic from sub-seeds. |
| **Match Engine Service** | Runs a single match end-to-end (the prior design), headless for batch or rendered for viewing. | Idempotent: `(teamA, teamB, seed) → result`. |
| **Analytics & Ratings Engine** | Elo/strength ratings, win probabilities, standings math, tiebreakers, projections. | Pure functions over state. |
| **Tournament State Store** | Authoritative tournament state: groups, fixtures, standings, bracket, results. | In-memory hot copy + persisted snapshots. |
| **Viewer / Replay Front-end** | Renders live matches or replays from recorded events. | The light, text-free Canvas2D view. |
| **LLM Gateway** | Single choke point for any LLM call: prompt templating, caching (keyed by seed), guardrails. | Keeps non-determinism contained and auditable. |

---

## 5. C4 Level 3 — Components

### 5.1 Tournament Orchestrator Service

```mermaid
flowchart TB
  subgraph TOUR["Tournament Orchestrator Service [Container]"]
    fsm["Lifecycle State Machine<br/>[Component]<br/>setup to groups to knockout to final"]
    policy["Tournament Policy / Rules<br/>[Component]<br/>format, group size, tiebreakers,<br/>extra-time, penalties"]
    draw["Draw Agent<br/>[Component]<br/>seeds pots, draws groups<br/>with confederation constraints"]
    sched["Scheduler Agent<br/>[Component]<br/>builds fixture list per round"]
    dispatch["Match Dispatcher<br/>[Component]<br/>queues fixtures, parallelizes a round"]
    progress["Progression / Bracket Manager<br/>[Component]<br/>standings, advancement, bracket"]
    aggregate["Result Aggregator<br/>[Component]<br/>collates stats, updates ratings, narrative"]
    bb["Tournament Blackboard<br/>[Component]<br/>shared tournament state"]
  end
  gen["Generation Service"]
  match["Match Engine Service"]
  ratings["Analytics & Ratings Engine"]
  tstate["Tournament State Store"]

  fsm -->|"needs teams"| gen
  fsm --> draw
  fsm --> sched
  fsm --> dispatch
  fsm --> progress
  policy -->|"rules"| draw
  policy -->|"rules"| progress
  draw -->|"groups"| bb
  sched -->|"fixtures"| bb
  dispatch -->|"run match"| match
  match -->|"result"| aggregate
  aggregate -->|"writes"| tstate
  aggregate -->|"update ratings"| ratings
  progress -->|"reads results & tiebreaks"| ratings
  progress -->|"advances teams"| bb
  bb -->|"snapshot to"| tstate
```

### 5.2 Generation Service

```mermaid
flowchart LR
  subgraph GEN["Generation Service [Container]"]
    ntg["National Team Generator Agent<br/>[Component]<br/>orchestrates per-nation build"]
    seed["Seed / RNG Provider<br/>[Component]<br/>deterministic sub-seeds per nation"]
    ident["Nation Identity & Style<br/>[Component]<br/>tier, footballing DNA, colors"]
    pgen["Player Generator<br/>[Component]<br/>position-weighted attributes"]
    cgen["Coach & Tactics Generator<br/>[Component]<br/>formation, aggression, line, tempo, press"]
    build["Team Builder & Validator<br/>[Component]<br/>fill slots, constraints, team rating"]
  end
  gw["LLM Gateway"]
  tstate["Tournament State Store"]

  seed -->|"sub-seed"| ntg
  ntg --> ident
  ident -->|"tier + DNA"| pgen
  ident -->|"tier + DNA"| cgen
  pgen -->|"roster"| build
  cgen -->|"coach profile"| build
  build -->|"validated team"| tstate
  ident -.->|"names / style text"| gw
```

The **Nation Identity & Style** component assigns a *tier* (which scales attribute means) and a *style DNA* (e.g., possession, high-press, counter, direct) that biases both the player attribute distribution and the coach profile — so generated teams play recognizably differently.

### 5.3 Match Engine Service (reuses the prior one-AI-per-team design)

```mermaid
flowchart LR
  caller["Match Dispatcher"]
  subgraph ME["Match Engine Service [Container]"]
    mo["Match Orchestrator<br/>[Component]<br/>kickoff, clock, restarts, end of match,<br/>extra time & penalties if drawn"]
    sim["Simulation Runtime<br/>[Component: fixed-timestep loop]"]
    phys["Physics Engine<br/>[Component]<br/>kinematics, collisions, ball"]
    toA["Team Orchestrator A<br/>[Component: AI = coach + 11 players]"]
    toB["Team Orchestrator B<br/>[Component: AI = coach + 11 players]"]
    world["Match World State [Component]"]
    rec["Event Recorder<br/>[Component]<br/>goals, shots, possession"]
  end
  caller -->|"simulate(teamA, teamB, seed)"| mo
  mo --> sim
  sim -->|"perceive + decide"| toA
  sim -->|"perceive + decide"| toB
  toA -->|"player commands"| phys
  toB -->|"player commands"| phys
  phys --> world
  sim --> world
  world --> rec
  mo -->|"final result + event log"| caller
```

Each **Team Orchestrator** is the three-layer agent from the previous design (slow Coach loop + fast Role-Allocator loop + per-player behaviour resolver, behind a pluggable decision policy). The Match Engine simply runs two of them against each other and reports the result — turning a *real-time, rendered* simulation into a *batch, headless* function the tournament can call 64 times.

---

## 6. Agent Catalog

| Agent | Phase | Trigger / Loop | Key tools | Output |
|---|---|---|---|---|
| **Tournament Orchestrator** | Run | Tournament lifecycle FSM | Draw, Scheduler, Dispatcher, Progression | Champion + full record |
| **Draw Agent** | Run | Once, after generation | Seed, Policy (pot/confederation rules) | Groups |
| **Scheduler Agent** | Run | Per round | Policy (round-robin / bracket) | Fixtures |
| **Match Dispatcher** | Run | Per round | Worker pool, Match Engine | Parallel match results |
| **Progression / Bracket Manager** | Run | After each round | Ratings (standings, tiebreakers) | Advancing teams, bracket |
| **Result Aggregator** | Run | Per match | Ratings, LLM Gateway (narrative) | Stats, updated ratings |
| **National Team Generator** | Build | Per nation | Seed, Identity, Player/Coach gen, Builder | One validated team |
| **Player Generator** | Build | Per player slot | Seed, attribute model | Player with attributes |
| **Coach & Tactics Generator** | Build | Per team | Seed, style DNA | Coach profile |
| **Team Builder & Validator** | Build | Per team | Formation rules, rating function | Match-ready team |
| **Team Orchestrator (×2 / match)** | Match | Per tick (fast) + per few sec (slow) | Decision Policy, blackboard | Player commands |
| **Commentary Agent** *(optional)* | Run | Per key event | LLM Gateway | Narrative text |

---

## 7. Tool Catalog

| Tool | Used by | Purpose | Deterministic |
|---|---|---|---|
| **Seeded RNG** | All generators, sim | Reproducible randomness from sub-seeds | Yes |
| **Attribute Model** | Player Generator | Map (position, tier, DNA) → attributes | Yes |
| **Match Engine `simulate()`** | Dispatcher | Run one match → result + events | Yes (per seed) |
| **Standings Calculator** | Progression | Points, GD, head-to-head tiebreaks | Yes |
| **Elo / Rating Updater** | Aggregator | Update strength after each match | Yes |
| **Bracket Builder** | Progression | Map qualifiers → knockout slots | Yes |
| **LLM Gateway call** | Generation, Commentary | Names, style, commentary, tactical hints | No (cached by seed) |

---

## 8. Dynamic Views

### 8.1 Tournament Lifecycle (state machine)

```mermaid
stateDiagram-v2
  [*] --> Setup
  Setup --> GeneratingTeams: config accepted
  GeneratingTeams --> Draw: all teams valid
  Draw --> GroupStage: groups drawn
  GroupStage --> GroupStage: next matchday
  GroupStage --> RoundOf16: standings final
  RoundOf16 --> QuarterFinals: winners advance
  QuarterFinals --> SemiFinals: winners advance
  SemiFinals --> Final: winners advance
  SemiFinals --> ThirdPlacePlayoff: losers
  Final --> Done: champion decided
  ThirdPlacePlayoff --> Done
  Done --> [*]
```

> Knockout matches resolve via a sub-procedure: regulation → extra time if drawn → penalty shootout if still drawn. The Match Orchestrator owns this so the tournament always receives a decisive result.

### 8.2 End-to-End Orchestration (sequence)

```mermaid
sequenceDiagram
  actor Op as Operator
  participant TO as Tournament Orchestrator
  participant GEN as Generation Service
  participant ST as Tournament State
  participant DSP as Match Dispatcher
  participant ME as Match Engine
  participant RT as Ratings Engine

  Op->>TO: start World Cup with seed and format
  TO->>GEN: generate N national teams
  GEN->>ST: store validated teams
  TO->>TO: draw groups via Draw Agent
  TO->>ST: persist groups and fixtures

  loop each group matchday
    TO->>DSP: dispatch matchday fixtures
    par matches run in parallel
      DSP->>ME: simulate match Team X vs Team Y
      ME-->>DSP: result, events, stats
    end
    DSP-->>TO: matchday results
    TO->>RT: update standings and ratings
  end

  TO->>TO: compute qualifiers and build bracket
  loop each knockout round
    TO->>DSP: dispatch round fixtures
    DSP->>ME: simulate match with ET and penalties if drawn
    ME-->>DSP: decisive result
    DSP-->>TO: round results
    TO->>ST: advance winners
  end

  TO->>ME: simulate the Final
  ME-->>TO: champion decided
  TO-->>Op: tournament complete with full record
```

### 8.3 Generation Flow (per nation)

```mermaid
flowchart LR
  a["Master seed + nation index"] --> b["Derive nation sub-seed"]
  b --> c["Assign tier + style DNA"]
  c --> d["Generate 23-player squad<br/>position-weighted attributes"]
  c --> e["Generate coach profile<br/>aligned to style DNA"]
  d --> f["Team Builder: pick XI,<br/>fill formation, validate"]
  e --> f
  f --> g["Compute team rating"]
  g --> h["Emit validated team to State Store"]
```

### 8.4 Round Parallelism

```mermaid
flowchart LR
  round["Round fixtures (independent)"] --> q["Match Queue"]
  q --> w1["Match Engine Worker 1"]
  q --> w2["Match Engine Worker 2"]
  q --> w3["Match Engine Worker N"]
  w1 --> agg["Result Collector"]
  w2 --> agg
  w3 --> agg
  agg --> prog["Progression Manager"]
```

---

## 9. Data Model

```mermaid
erDiagram
  TOURNAMENT ||--o{ GROUP : contains
  TOURNAMENT ||--o{ ROUND : has
  TOURNAMENT ||--|| TEAM : crowns_champion
  GROUP ||--o{ TEAM : seeds
  ROUND ||--o{ MATCH : schedules
  GROUP ||--o{ MATCH : stages
  TEAM ||--o{ PLAYER : fields
  TEAM ||--|| COACH : led_by
  MATCH ||--o{ MATCH_EVENT : produces
  MATCH }o--|| TEAM : home
  MATCH }o--|| TEAM : away
  TEAM ||--o{ STANDING : tracked_by

  TOURNAMENT {
    string id
    int seed
    string format
    string status
  }
  TEAM {
    string id
    string nation
    int tier
    float rating
    string styleDNA
  }
  PLAYER {
    string id
    string role
    float pace
    float passing
    float shooting
    float defending
    float stamina
  }
  COACH {
    string formation
    float aggression
    float lineHeight
    float tempo
    float pressing
  }
  MATCH {
    string id
    string phase
    int scoreHome
    int scoreAway
    bool decidedByPenalties
  }
  MATCH_EVENT {
    float t
    string type
    string team
  }
  STANDING {
    int played
    int points
    int gf
    int ga
  }
```

---

## 10. Orchestration, State & Memory

- **Blackboard pattern.** The Tournament Blackboard holds the single source of truth during a run; agents are stateless functions over it. The blackboard is snapshotted to the State Store after every round, so a run can be paused, resumed, or replayed.
- **Event bus.** Matches emit events (goal, full-time, qualifier-decided). The orchestrator subscribes and reacts (update standings, advance bracket) rather than polling.
- **Memory tiers.** *Short-term* = current match world state (discarded after the match, except the event log). *Long-term* = tournament state, ratings history, generated rosters (persisted).
- **Idempotency.** `simulate(teamA, teamB, seed)` and every generator are pure given their seed, so re-running a failed step is safe and produces identical output.

---

## 11. Determinism & Reproducibility

A single **master seed** deterministically derives all sub-seeds:

```
master_seed
 ├─ nation_seed[i]      = hash(master_seed, "nation", i)
 ├─ draw_seed           = hash(master_seed, "draw")
 └─ match_seed[m]       = hash(master_seed, "match", round, fixtureId)
```

Given the same master seed and config, the framework reproduces the **identical tournament** — same teams, same draw, same scorelines, same champion. LLM outputs (names, commentary) are cached by their seed-derived key so even the "creative" layer is reproducible across runs.

---

## 12. Scale & Performance

- A 32-team cup = **48 group matches + 16 knockout matches = 64 matches**. Each headless match runs far faster than real time, and group/round matches are independent → run them on a **worker pool** (Node worker threads, web workers, or serverless fan-out).
- The expensive part is *never* an LLM in the loop — it is bounded physics over ~22 bodies per match. End-to-end a full cup completes in seconds to low minutes headless.
- The Viewer only renders matches the operator chooses to watch; the rest run headless and are replayable from their event logs on demand.

---

## 13. Suggested Technology Mapping

| Concern | Suggested implementation |
|---|---|
| Orchestration core / FSM | LangGraph-style state graph, or a durable workflow engine for pause/resume |
| Agent runtime & tool dispatch | Lightweight in-process registry; tools as typed functions |
| Match Engine | The existing single-file canvas sim, refactored to run **headless in Node** (no DOM) for batch and **in-browser** for rendering — one codebase, two entry points |
| State store | In-memory hot copy + JSON/SQLite snapshots (Postgres if multi-run history is needed) |
| Parallel execution | Worker pool / web workers / serverless fan-out keyed by `match_seed` |
| LLM Gateway | A single client (e.g., Claude API) with prompt templates, seed-keyed cache, and output guardrails |
| Front-end | Reuse the light, text-free Canvas2D viewer; feed it either live frames or a recorded event log |

---

## 14. Honest Assessment & Risks

- **"Agentic" here means hierarchical orchestration + pluggable policy agents — not an LLM calling tools in a loop to run physics.** If you only ever want one fixed ruleset, a plain workflow engine would do the same job with less ceremony. The agentic framing earns its keep when you want: swappable decision policies (heuristic vs RL), per-nation asymmetric tactics, narrative generation, and easy extension to new tournament formats.
- **Keep the LLM off the hot path.** Per-tick decisions must stay heuristic/RL for determinism and speed. Any LLM use belongs in generation flavor, commentary, or the Coach's slow loop — always cached.
- **Tiebreakers and edge cases are where tournaments get messy** (three-way ties on points, fair-play tiebreaks, drawn knockouts). Encode them explicitly in **Tournament Policy** and unit-test them, rather than letting an agent improvise.
- **Determinism is a feature, protect it.** Any nondeterministic source (unordered parallelism writing shared state, `Math.random`, unseeded LLM calls) will silently break reproducibility. Funnel all randomness through the Seed Provider and all LLM calls through the Gateway.

---

## 15. Incremental Build Roadmap

1. **Headless Match Engine** — refactor the simulation to run without a DOM and return `{ result, events }`.
2. **Generation Service** — deterministic nation/player/coach/team generation with tiers and style DNA.
3. **Tournament Orchestrator** — lifecycle FSM: draw → group standings → bracket → final.
4. **Analytics & Ratings** — Elo, standings math, tiebreakers, projections.
5. **Persistence & replay** — snapshot state, record/replay event logs.
6. **Parallel execution** — worker pool for concurrent matches per round.
7. **Viewer integration** — watch any match live or replay from its log.
8. **Optional LLM layer** — names, commentary, tactical hints via the Gateway.
