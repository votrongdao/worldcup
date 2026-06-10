# AI Agentic World Cup — Project Scaffold

Materialized from the implementation blueprint. Two apps + infra:

- `backend/`  — Python / FastAPI, hexagonal (ports & adapters), deterministic core.
- `frontend/` — React + Vite + TypeScript + TanStack (Query / Router / Table) + SignalR.
- `backend/azure/` — Bicep placeholders for Azure (Container Apps, Service Bus, Postgres, Redis, Blob, SignalR).
- `docs/` — the architecture documents (C4 overview, comprehensive arc42, implementation blueprint).

## Layout principle
Dependencies point inward: `domain` + `match_engine` depend on nothing external;
`orchestrator`/`generation`/`ratings` depend on `domain` + `infra.ports`;
Azure adapters in `infra/` implement those ports. Swap Azure for anything by
re-implementing the ports — the deterministic core never changes.

## Run (local, after filling the TODOs)
Backend API:    `uvicorn src.app.main:app --reload`   (from backend/)
Backend worker: `python -m src.workers.main`           (from backend/)
Frontend:       `npm install && npm run dev`           (from frontend/)

## Status
Load-bearing files (Pydantic contracts, seed core, ports, policy interfaces,
FastAPI wiring, TanStack hooks, canvas renderer) are implemented. Files marked
`# TODO` / `// TODO` are intentional stubs with a one-line responsibility — the
structure is complete and compiles; the algorithms are the build work.

## Reproducibility
One master seed -> hashed sub-seeds (`src/seed/provider.py`) -> identical run.
`src/observability/run_hash.py` hashes the ordered event log to verify it.
