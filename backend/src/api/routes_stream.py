"""Live stream negotiate endpoint.

In the cloud this returns an Azure SignalR url + access token. Locally, live frame
streaming is not wired (the physics path that produces per-frame positions is still
stubbed), so the client should fall back to event-log replay via /matches/{id}/events.
"""
from __future__ import annotations
from fastapi import APIRouter

from src.app.deps import get_deps

router = APIRouter(tags=["stream"])


@router.post("/negotiate")
async def negotiate(match_id: str) -> dict:
    deps = get_deps()
    if deps.settings.backend.lower() == "azure":
        sr = deps.signalr
        if hasattr(sr, "negotiate"):
            return sr.negotiate(match_id)  # type: ignore[attr-defined]
    # Local/memory: no SignalR emulator — tell the client to replay instead.
    return {"mode": "replay", "events": f"/matches/{match_id}/events"}
