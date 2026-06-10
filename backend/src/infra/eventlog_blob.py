"""EventLog adapter: append-only, newline-delimited JSON in Azure Blob (Azurite local).

One append blob per stream (a match id). Each domain/match event is one JSON line,
preserving order for replay. Works identically against Azurite and Azure Storage.
"""
from __future__ import annotations
import json

from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from azure.storage.blob.aio import BlobServiceClient


class BlobEventLog:
    def __init__(self, conn: str, container: str = "eventlogs") -> None:
        self._svc = BlobServiceClient.from_connection_string(conn)
        self._container = container
        self._ready = False

    async def _ensure_container(self) -> None:
        if self._ready:
            return
        try:
            await self._svc.create_container(self._container)
        except ResourceExistsError:
            pass
        self._ready = True

    async def append(self, stream: str, events: list) -> None:
        await self._ensure_container()
        blob = self._svc.get_blob_client(self._container, f"{stream}.ndjson")
        try:
            await blob.create_append_blob()
        except ResourceExistsError:
            pass
        lines = "".join(
            json.dumps(e.model_dump() if hasattr(e, "model_dump") else e, default=str) + "\n"
            for e in events
        )
        if lines:
            await blob.append_block(lines.encode("utf-8"))

    async def read(self, stream: str) -> list:
        await self._ensure_container()
        blob = self._svc.get_blob_client(self._container, f"{stream}.ndjson")
        try:
            downloaded = await blob.download_blob()
            data = await downloaded.readall()
        except ResourceNotFoundError:
            return []
        return [json.loads(line) for line in data.decode("utf-8").splitlines() if line]

    async def close(self) -> None:
        await self._svc.close()
