"""Cache adapter: Azure Cache for Redis (blackboard + pub/sub)."""
from __future__ import annotations
from typing import Any
from .ports import Cache


class RedisCache(Cache):
    def __init__(self, url: str) -> None:
        self._url = url  # TODO: redis.asyncio.from_url(url)

    async def get(self, key: str) -> Any: ...
    async def set(self, key: str, value: Any) -> None: ...
