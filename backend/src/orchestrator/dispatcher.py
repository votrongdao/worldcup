"""MatchDispatcher: enqueue match requests onto the MatchQueue port."""
from __future__ import annotations
import asyncio
from src.domain.match import MatchRequest
from src.infra.ports import MatchQueue


class MatchDispatcher:
    def __init__(self, queue: MatchQueue) -> None:
        self._queue = queue

    async def dispatch(self, requests: list[MatchRequest]) -> list[str]:
        """Enqueue every request (in parallel) and return their match ids."""
        await asyncio.gather(*(self._queue.enqueue(r) for r in requests))
        return [r.match_id for r in requests]
