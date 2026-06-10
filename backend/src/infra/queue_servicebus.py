"""MatchQueue adapter backed by Azure Service Bus."""
from __future__ import annotations
from src.domain.match import MatchRequest
from .ports import MatchQueue


class ServiceBusQueue(MatchQueue):
    def __init__(self, conn: str, queue_name: str = "matches") -> None:
        self._conn = conn; self._queue = queue_name  # TODO: ServiceBusClient

    async def enqueue(self, req: MatchRequest) -> None:
        ...  # TODO: send_messages(ServiceBusMessage(req.model_dump_json()))

    async def consume(self) -> MatchRequest:
        ...  # TODO: receive + parse_raw; complete on success (idempotent by seed)
        raise NotImplementedError
