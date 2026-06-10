"""Dependency wiring: assemble the adapter set for the configured backend.

``WC_BACKEND`` chooses the implementations behind each port. The rest of the app
depends only on the ports, so nothing else changes between memory / local / azure.
"""
from __future__ import annotations
from dataclasses import dataclass
from functools import lru_cache

from src.infra.ports import (
    Cache,
    EventBus,
    EventLog,
    LlmGateway,
    MatchQueue,
    ResultBus,
    SignalRPort,
    StateStore,
)
from .config import Settings


@dataclass
class Deps:
    settings: Settings
    queue: MatchQueue
    bus: ResultBus
    store: StateStore
    log: EventLog
    cache: Cache
    signalr: SignalRPort
    llm: LlmGateway
    events: EventBus


def _build(settings: Settings) -> Deps:
    backend = settings.backend.lower()

    if backend == "memory":
        from src.infra.memory import get_backend
        from src.infra.llm_gateway import AzureOpenAIGateway, NullLlmGateway

        mem = get_backend()
        llm: LlmGateway = (AzureOpenAIGateway(settings, mem)
                           if settings.llm_enabled else NullLlmGateway())
        return Deps(settings, queue=mem, bus=mem, store=mem, log=mem,
                    cache=mem, signalr=mem, llm=llm, events=mem)

    if backend == "local":
        from src.infra.redis_backend import RedisBackend
        from src.infra.store_postgres import PostgresStore
        from src.infra.eventlog_blob import BlobEventLog
        from src.infra.llm_gateway import AzureOpenAIGateway, NullLlmGateway

        rb = RedisBackend(settings.redis_url)
        llm = (AzureOpenAIGateway(settings, rb)
               if settings.llm_enabled else NullLlmGateway())
        return Deps(settings, queue=rb, bus=rb, cache=rb, signalr=rb, events=rb,
                    store=PostgresStore(settings.pg_dsn),
                    log=BlobEventLog(settings.blob_conn), llm=llm)

    # backend == "azure": native Azure adapters (Service Bus / Postgres / Blob / SignalR).
    from src.infra.redis_backend import RedisBackend
    from src.infra.queue_servicebus import ServiceBusQueue
    from src.infra.store_postgres import PostgresStore
    from src.infra.eventlog_blob import BlobEventLog
    from src.infra.signalr import AzureSignalR
    from src.infra.llm_gateway import AzureOpenAIGateway, NullLlmGateway

    rb = RedisBackend(settings.redis_url)
    queue = ServiceBusQueue(settings.servicebus_conn)
    llm = (AzureOpenAIGateway(settings, rb)
           if settings.llm_enabled else NullLlmGateway())
    return Deps(settings, queue=queue, bus=rb, cache=rb, events=rb,
                signalr=AzureSignalR(settings.signalr_conn),
                store=PostgresStore(settings.pg_dsn),
                log=BlobEventLog(settings.blob_conn), llm=llm)


@lru_cache(maxsize=1)
def get_deps() -> Deps:
    """Process-wide singleton so memory state (and pooled clients) are shared."""
    return _build(Settings())
