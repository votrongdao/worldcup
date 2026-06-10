"""SignalRPort adapter: push live frames via Azure SignalR Service."""
from __future__ import annotations
from .ports import SignalRPort


class AzureSignalR(SignalRPort):
    def __init__(self, conn: str, hub: str = "match") -> None:
        self._conn = conn; self._hub = hub

    async def push(self, group: str, frame: dict) -> None:
        ...  # TODO: REST broadcast to group (match id)

    def negotiate(self, group: str) -> dict:
        ...  # TODO: return {url, accessToken} for the browser client
        return {}
