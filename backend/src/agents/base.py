"""Agent / Tool / RunContext framework primitives (structural typing)."""
from __future__ import annotations
from typing import Any, Protocol, runtime_checkable
from src.domain.events import DomainEvent


@runtime_checkable
class RunContext(Protocol):
    seed: int
    def emit(self, event: DomainEvent) -> None: ...


class Tool(Protocol):
    name: str
    deterministic: bool
    def invoke(self, input: Any, ctx: RunContext) -> Any: ...


class Agent(Protocol):
    name: str
    async def run(self, input: Any, ctx: RunContext) -> Any: ...
