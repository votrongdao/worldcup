"""Worker process entrypoint: a competing consumer of the match queue."""
from __future__ import annotations
import asyncio
import logging

from src.app.deps import get_deps
from .match_worker import handle

log = logging.getLogger("worker")


async def worker_loop(deps=None, *, name: str = "worker") -> None:
    """Consume match jobs forever, simulating each and publishing the result."""
    d = deps or get_deps()
    log.info("%s started (backend=%s)", name, d.settings.backend)
    while True:
        req = await d.queue.consume()
        try:
            await handle(req, d.log, d.bus, d.signalr)
        except Exception:  # never let one bad job kill the consumer
            log.exception("match %s failed", req.match_id)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    deps = get_deps()
    n = max(1, deps.settings.worker_concurrency)
    async def _run() -> None:
        await asyncio.gather(*(worker_loop(deps, name=f"worker-{i}") for i in range(n)))
    asyncio.run(_run())


if __name__ == "__main__":
    main()
