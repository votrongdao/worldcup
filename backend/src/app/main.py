"""FastAPI application factory: mounts routers, middleware, and (memory mode) workers."""
from __future__ import annotations
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.app.deps import get_deps
from src.app.logging import configure
from src.api import (
    routes_llm,
    routes_matches,
    routes_stream,
    routes_teams,
    routes_tournaments,
)
from src.workers.main import worker_loop


@asynccontextmanager
async def lifespan(app: FastAPI):
    deps = get_deps()
    tasks: list[asyncio.Task] = []
    # In memory mode there is no separate worker container, so run workers in-process.
    if deps.settings.backend.lower() == "memory":
        n = max(1, deps.settings.worker_concurrency)
        tasks = [asyncio.create_task(worker_loop(deps, name=f"inproc-{i}"))
                 for i in range(n)]
    try:
        yield
    finally:
        for t in tasks:
            t.cancel()


def create_app() -> FastAPI:
    configure()
    app = FastAPI(title="AI Agentic World Cup Orchestrator", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
    )
    app.include_router(routes_tournaments.router)
    app.include_router(routes_matches.router)
    app.include_router(routes_teams.router)
    app.include_router(routes_stream.router)
    app.include_router(routes_llm.router)

    @app.get("/health", tags=["meta"])
    async def health() -> dict:
        return {"status": "ok", "backend": get_deps().settings.backend}

    return app


app = create_app()
