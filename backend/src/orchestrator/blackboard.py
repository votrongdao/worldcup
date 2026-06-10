"""Shared tournament state, backed by the Cache port (Redis in Azure)."""
from __future__ import annotations
from typing import Any
from src.infra.ports import Cache


class Blackboard:
    def __init__(self, cache: Cache) -> None: self._cache = cache
    async def get(self, key: str) -> Any: return await self._cache.get(key)
    async def set(self, key: str, value: Any) -> None: await self._cache.set(key, value)
