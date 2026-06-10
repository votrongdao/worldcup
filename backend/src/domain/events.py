"""Append-only domain event taxonomy (event sourcing)."""
from __future__ import annotations
from typing import Any
from pydantic import BaseModel


class DomainEvent(BaseModel):
    seq: int
    t: str
    type: str
    payload: dict[str, Any] = {}
