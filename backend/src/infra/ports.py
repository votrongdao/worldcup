"""Driven ports. Azure adapters implement these; the app depends only on them."""
from __future__ import annotations
from typing import Any, Protocol
from src.domain.match import MatchRequest, MatchResult
from src.domain.tournament import Tournament
from src.domain.events import DomainEvent


class MatchQueue(Protocol):
    async def enqueue(self, req: MatchRequest) -> None: ...
    async def consume(self) -> MatchRequest: ...


class ResultBus(Protocol):
    """Workers publish finished matches here; the orchestrator awaits them by id."""
    async def publish(self, result: MatchResult) -> None: ...
    async def result(self, match_id: str) -> MatchResult: ...


class StateStore(Protocol):
    async def save(self, t: Tournament) -> None: ...
    async def load(self, tournament_id: str) -> Tournament: ...


class EventLog(Protocol):
    async def append(self, stream: str, events: list[DomainEvent]) -> None: ...
    async def read(self, stream: str) -> list[DomainEvent]: ...


class Cache(Protocol):
    async def get(self, key: str) -> Any: ...
    async def set(self, key: str, value: Any) -> None: ...


class SignalRPort(Protocol):
    async def push(self, group: str, frame: dict) -> None: ...


class EventBus(Protocol):
    """Agentic event bus: agents emit domain events; subscribers read recent history.

    Locally backed by Redis (pub/sub + a capped list per topic) or in-memory for tests.
    """
    async def emit(self, topic: str, event: dict) -> None: ...
    async def history(self, topic: str, limit: int = 200) -> list[dict]: ...


class LlmGateway(Protocol):
    async def complete(self, prompt: str, seed_key: str) -> str: ...
