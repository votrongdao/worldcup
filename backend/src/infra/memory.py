"""In-process adapter set: one object satisfying every driven port.

Used by ``WC_BACKEND=memory`` (and the tests). Because the ports are structural
Protocols, a single object can stand in for the queue, result bus, cache, event
log, state store and SignalR push — all sharing process memory. The API process
runs its own worker tasks against this same instance (see ``app.main`` lifespan).
"""
from __future__ import annotations
import asyncio
from typing import Any

from src.domain.events import DomainEvent
from src.domain.match import MatchRequest, MatchResult
from src.domain.tournament import Tournament


class InMemoryBackend:
    def __init__(self) -> None:
        self._queue: asyncio.Queue[MatchRequest] = asyncio.Queue()
        self._results: dict[str, asyncio.Future[MatchResult]] = {}
        self._cache: dict[str, Any] = {}
        self._streams: dict[str, list[DomainEvent]] = {}
        self._store: dict[str, Tournament] = {}
        self._frames: dict[str, list[dict]] = {}
        self._events_log: dict[str, list[dict]] = {}

    # --- EventBus ------------------------------------------------------
    async def emit(self, topic: str, event: dict) -> None:
        self._events_log.setdefault(topic, []).append(event)

    async def history(self, topic: str, limit: int = 200) -> list[dict]:
        return list(self._events_log.get(topic, []))[-limit:]

    # --- MatchQueue ----------------------------------------------------
    async def enqueue(self, req: MatchRequest) -> None:
        await self._queue.put(req)

    async def consume(self) -> MatchRequest:
        return await self._queue.get()

    # --- ResultBus -----------------------------------------------------
    def _future(self, match_id: str) -> "asyncio.Future[MatchResult]":
        fut = self._results.get(match_id)
        if fut is None:
            fut = asyncio.get_event_loop().create_future()
            self._results[match_id] = fut
        return fut

    async def publish(self, result: MatchResult) -> None:
        fut = self._future(result.match_id)
        if not fut.done():
            fut.set_result(result)

    async def result(self, match_id: str) -> MatchResult:
        return await self._future(match_id)

    # --- Cache ---------------------------------------------------------
    async def get(self, key: str) -> Any:
        return self._cache.get(key)

    async def set(self, key: str, value: Any) -> None:
        self._cache[key] = value

    # --- EventLog ------------------------------------------------------
    async def append(self, stream: str, events: list) -> None:
        self._streams.setdefault(stream, []).extend(events)

    async def read(self, stream: str) -> list:
        return list(self._streams.get(stream, []))

    # --- StateStore ----------------------------------------------------
    async def save(self, t: Tournament) -> None:
        self._store[t.id] = t.model_copy(deep=True)

    async def load(self, tournament_id: str) -> Tournament:
        return self._store[tournament_id]

    # --- SignalRPort ---------------------------------------------------
    async def push(self, group: str, frame: dict) -> None:
        self._frames.setdefault(group, []).append(frame)


# Process-wide singleton so the API, the orchestrator and the in-process
# worker tasks all share the same queues and stores.
_SINGLETON: InMemoryBackend | None = None


def get_backend() -> InMemoryBackend:
    global _SINGLETON
    if _SINGLETON is None:
        _SINGLETON = InMemoryBackend()
    return _SINGLETON
