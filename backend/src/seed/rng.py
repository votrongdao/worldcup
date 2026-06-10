"""Seeded LCG PRNG. Simple and portable for cross-language parity."""
from __future__ import annotations


class SeededRng:
    def __init__(self, seed: int) -> None:
        self._s = seed & 0xFFFFFFFF

    def next_u32(self) -> int:
        self._s = (1664525 * self._s + 1013904223) & 0xFFFFFFFF
        return self._s

    def random(self) -> float:
        return self.next_u32() / 0x100000000

    def uniform(self, lo: float, hi: float) -> float:
        return lo + (hi - lo) * self.random()

    def randint(self, lo: int, hi: int) -> int:
        return lo + int(self.random() * (hi - lo + 1))
