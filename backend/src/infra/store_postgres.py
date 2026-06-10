"""StateStore adapter: tournament snapshots in PostgreSQL (JSONB), async SQLAlchemy."""
from __future__ import annotations
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from src.domain.tournament import Tournament

_DDL = text("""
CREATE TABLE IF NOT EXISTS tournaments (
    id          TEXT PRIMARY KEY,
    phase       TEXT NOT NULL,
    run_hash    TEXT NOT NULL DEFAULT '',
    data        JSONB NOT NULL,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
)
""")

_UPSERT = text("""
INSERT INTO tournaments (id, phase, run_hash, data, updated_at)
VALUES (:id, :phase, :run_hash, CAST(:data AS JSONB), now())
ON CONFLICT (id) DO UPDATE
    SET phase = EXCLUDED.phase,
        run_hash = EXCLUDED.run_hash,
        data = EXCLUDED.data,
        updated_at = now()
""")

_SELECT = text("SELECT data FROM tournaments WHERE id = :id")


class PostgresStore:
    def __init__(self, dsn: str) -> None:
        self._engine: AsyncEngine = create_async_engine(dsn, pool_pre_ping=True)
        self._ready = False

    async def _ensure(self) -> None:
        if not self._ready:
            async with self._engine.begin() as conn:
                await conn.execute(_DDL)
            self._ready = True

    async def save(self, t: Tournament) -> None:
        await self._ensure()
        async with self._engine.begin() as conn:
            await conn.execute(_UPSERT, {
                "id": t.id, "phase": t.phase.value, "run_hash": t.run_hash,
                "data": t.model_dump_json(),
            })

    async def load(self, tournament_id: str) -> Tournament:
        await self._ensure()
        async with self._engine.connect() as conn:
            row = (await conn.execute(_SELECT, {"id": tournament_id})).first()
        if row is None:
            raise KeyError(f"tournament {tournament_id!r} not found")
        return Tournament.model_validate(row[0])
