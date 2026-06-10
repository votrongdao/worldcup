"""RunSupervisor: snapshot/resume for pause and crash recovery."""
from __future__ import annotations
from src.infra.ports import StateStore
from src.domain.tournament import Tournament


class RunSupervisor:
    def __init__(self, store: StateStore) -> None: self._store = store

    async def snapshot(self, t: Tournament) -> None: await self._store.save(t)
    async def resume(self, tournament_id: str) -> Tournament:
        return await self._store.load(tournament_id)
