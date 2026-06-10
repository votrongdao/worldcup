"""Deterministic run hash: hash of the ordered event log (reproducibility check)."""
from __future__ import annotations
import hashlib
from src.domain.events import DomainEvent


def run_hash(events: list[DomainEvent]) -> str:
    h = hashlib.sha256()
    for e in events:
        h.update(f"{e.seq}:{e.type}:{e.payload}".encode())
    return h.hexdigest()
