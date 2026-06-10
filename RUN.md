# Running locally

Two ways to run, depending on whether you want Docker.

## 1) Full stack in Docker (recommended)

Brings up Postgres + Redis + Azurite + the FastAPI API + a match worker + the
React frontend. Requires **Docker Desktop** running.

```powershell
# from the repo root
.\run-local.ps1            # build + start everything, wait for health, print URLs
.\run-local.ps1 demo       # also simulate a 32-team World Cup and print the champion
```

| URL | What |
|-----|------|
| http://localhost:5173 | Frontend (nginx, proxies `/api` to the API) |
| http://localhost:8000 | API |
| http://localhost:8000/docs | Swagger UI |

Other commands:

```powershell
.\run-local.ps1 ps                      # container status
.\run-local.ps1 logs -Service worker    # follow a service's logs
.\run-local.ps1 restart                 # rebuild + restart api + worker after code edits
.\run-local.ps1 down                    # stop (keeps data)
.\run-local.ps1 clean                   # stop and delete the data volumes
.\run-local.ps1 demo -Teams 16 -Groups 4 -Seed 99
```

If you prefer raw Docker:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

### How it fits together
`POST /tournaments` starts the **orchestrator** (a FastAPI background task). It
generates teams, runs the draw, builds round-robin group fixtures and the knockout
bracket, and **dispatches each match onto the Redis queue**. The **worker**
container consumes jobs, runs the deterministic match engine, appends the event log
to **Azurite (blob)**, and publishes the result back on Redis. The orchestrator
awaits results, updates standings, and snapshots the whole tournament to
**Postgres**. The frontend reads it all over REST.

The queue/result-bus/cache/SignalR are backed by **Redis** locally (standing in for
Azure Service Bus + SignalR); the hexagonal ports make that swap invisible to the
core. Selected by `WC_BACKEND=local`.

## 2) No Docker — single process (memory mode)

Everything (API + in-process workers + in-memory store/queue/log) runs in one
process. Great for quick iteration; nothing external needed.

```powershell
cd backend
pip install -e ".[dev]"
$env:WC_BACKEND = "memory"
uvicorn src.app.main:app --reload      # http://localhost:8000

# in another shell:
curl -X POST http://localhost:8000/tournaments -H "content-type: application/json" `
  -d '{\"config\":{\"teams\":32,\"groups\":8,\"perGroup\":4,\"advancePerGroup\":2,\"seed\":2026}}'
curl http://localhost:8000/tournaments/wc-2026
curl http://localhost:8000/tournaments/wc-2026/standings
```

Run the tests:

```powershell
cd backend
pytest -q
```

## Enabling Azure AI Foundry models

The simulation is **fully deterministic without any LLM** — Foundry is optional
(used for commentary/flavour). To turn it on, edit `.env`:

```dotenv
WC_LLM_ENABLED=true
WC_AOAI_ENDPOINT=https://<your-resource>.openai.azure.com
WC_AOAI_DEPLOYMENT=<your-deployment-name>     # the deployment, not the base model id
WC_AOAI_API_VERSION=2024-10-21

# Auth — choose ONE:
WC_AOAI_API_KEY=<key>          # API key, OR
# leave WC_AOAI_API_KEY blank to use Entra ID (DefaultAzureCredential / Managed Identity)
```

Then restart: `.\run-local.ps1 restart`. Completions are cached by a deterministic
`seed_key`, so reruns of the same tournament stay reproducible.

## Key API endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/tournaments` | create + start a run (returns `{id}`) |
| `GET`  | `/tournaments/{id}` | status, phase, run hash, champion |
| `GET`  | `/tournaments/{id}/standings` | group tables |
| `GET`  | `/tournaments/{id}/bracket` | knockout bracket |
| `GET`  | `/tournaments/{id}/teams` | generated teams |
| `GET`  | `/tournaments/{id}/matches` | match summaries |
| `GET`  | `/matches/{id}/events` | ordered event log (replay) |

## Notes / current limits

- **Live frame streaming** (the animated pitch canvas) is not wired locally: there
  is no Azure SignalR emulator, and the per-player physics that would produce frames
  is still a stub. `POST /negotiate` returns a replay pointer; use
  `/matches/{id}/events` for the match timeline.
- The frontend image builds with `vite build` (esbuild) so a strict `tsc -b` does
  not block it.
- A worker that crashes mid-match would leave the orchestrator awaiting that match's
  result; failures are logged. Fine for local runs.
