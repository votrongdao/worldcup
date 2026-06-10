"""Redis-backed local bus: MatchQueue + ResultBus + Cache + SignalR push.

This stands in for Azure Service Bus + Azure SignalR in the local Docker stack.
The hexagonal design makes the swap transparent — the orchestrator and worker see
only the ports. A Redis list gives blocking, at-least-once job semantics (``BRPOP``);
match results come back on a per-match reply list; live frames fan out via pub/sub.
"""
from __future__ import annotations
import asyncio
import json
from typing import Any

import redis.asyncio as redis

from src.domain.match import MatchRequest, MatchResult

_QUEUE_KEY = "q:matches"
_RESULT_PREFIX = "result:"
_FRAME_CHANNEL = "frames:"
_EVENT_PREFIX = "events:"
_RESULT_TTL = 3600   # seconds a result waits for its consumer
_POLL = 0.1          # seconds between empty RPOP polls


class RedisBackend:
    def __init__(self, url: str) -> None:
        # Non-blocking RPOP polling (below) means connections are used constantly and
        # never sit idle, so Docker Desktop/WSL2 NAT can't drop them mid-read — the
        # failure mode a blocking BRPOP hits. keepalive is belt-and-suspenders.
        self._r = redis.from_url(
            url, decode_responses=True, socket_keepalive=True,
            health_check_interval=30,
        )

    # --- MatchQueue ----------------------------------------------------
    async def enqueue(self, req: MatchRequest) -> None:
        await self._r.lpush(_QUEUE_KEY, req.model_dump_json())

    async def consume(self) -> MatchRequest:
        while True:
            raw = await self._r.rpop(_QUEUE_KEY)
            if raw is not None:
                return MatchRequest.model_validate_json(raw)
            await asyncio.sleep(_POLL)

    # --- ResultBus -----------------------------------------------------
    async def publish(self, result: MatchResult) -> None:
        key = _RESULT_PREFIX + result.match_id
        await self._r.lpush(key, result.model_dump_json())
        await self._r.expire(key, _RESULT_TTL)

    async def result(self, match_id: str) -> MatchResult:
        key = _RESULT_PREFIX + match_id
        while True:
            raw = await self._r.rpop(key)
            if raw is not None:
                return MatchResult.model_validate_json(raw)
            await asyncio.sleep(_POLL)

    # --- Cache ---------------------------------------------------------
    async def get(self, key: str) -> Any:
        raw = await self._r.get(key)
        return json.loads(raw) if raw is not None else None

    async def set(self, key: str, value: Any) -> None:
        await self._r.set(key, json.dumps(value))

    # --- SignalRPort ---------------------------------------------------
    async def push(self, group: str, frame: dict) -> None:
        await self._r.publish(_FRAME_CHANNEL + group, json.dumps(frame))

    # --- EventBus ------------------------------------------------------
    async def emit(self, topic: str, event: dict) -> None:
        key = _EVENT_PREFIX + topic
        payload = json.dumps(event)
        await self._r.rpush(key, payload)
        await self._r.ltrim(key, -500, -1)        # keep the last 500 events
        await self._r.expire(key, 86400)
        await self._r.publish("ev:" + topic, payload)   # realtime fan-out

    async def history(self, topic: str, limit: int = 200) -> list[dict]:
        raw = await self._r.lrange(_EVENT_PREFIX + topic, -limit, -1)
        return [json.loads(x) for x in raw]

    async def close(self) -> None:
        await self._r.aclose()
