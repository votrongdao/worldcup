"""Shared tournament state, backed by the Cache port (Redis locally / in Azure).

The blackboard is the hot single-source-of-truth during a run: the orchestrator
writes a compact live status here on every phase change (durable snapshots still go
to the StateStore via the RunSupervisor). Agents read/write it instead of holding
critical state in their own heads, which keeps them stateless and replayable.
"""
from __future__ import annotations
from typing import Any, Optional

from src.infra.ports import Cache


class Blackboard:
    def __init__(self, cache: Cache) -> None:
        self._cache = cache

    async def get(self, key: str) -> Any:
        return await self._cache.get(key)

    async def set(self, key: str, value: Any) -> None:
        await self._cache.set(key, value)

    async def set_status(self, tournament_id: str, status: dict) -> None:
        await self._cache.set(f"hot:{tournament_id}", status)

    async def get_status(self, tournament_id: str) -> Optional[dict]:
        return await self._cache.get(f"hot:{tournament_id}")
