"""Deterministic sub-seed derivation. Every random decision derives from here."""
from __future__ import annotations
import hashlib


def sub_seed(master: int, *path: object) -> int:
    """Stable 32-bit sub-seed from a master seed and a path."""
    key = str(master) + "|" + "|".join(str(p) for p in path)
    return int.from_bytes(hashlib.sha256(key.encode()).digest()[:4], "big")
