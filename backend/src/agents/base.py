"""Agent / Tool / RunContext framework primitives (structural typing) + a concrete
RunContext that carries the seed and emits domain events onto the EventBus."""
from __future__ import annotations
from typing import Any, Optional, Protocol, runtime_checkable

from src.infra.ports import EventBus


@runtime_checkable
class RunContext(Protocol):
    seed: int
    async def emit(self, type_: str, **payload: Any) -> None: ...


class Tool(Protocol):
    name: str
    deterministic: bool
    def invoke(self, input: Any, ctx: "RunContext") -> Any: ...


class Agent(Protocol):
    name: str
    async def run(self, input: Any, ctx: "RunContext") -> Any: ...


class TournamentRunContext:
    """Concrete RunContext: seed + a topic-scoped emit() onto the event bus."""

    def __init__(self, seed: int, bus: Optional[EventBus], topic: str) -> None:
        self.seed = seed
        self._bus = bus
        self._topic = topic

    async def emit(self, type_: str, **payload: Any) -> None:
        if self._bus is not None:
            await self._bus.emit(self._topic, {"type": type_, **payload})
