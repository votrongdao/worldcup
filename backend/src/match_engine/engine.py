"""Match Engine facade. The only entry point workers call."""
from __future__ import annotations
from src.domain.match import MatchRequest, MatchResult
from .runtime import SimulationRuntime


class MatchEngine:
    def __init__(self, runtime: SimulationRuntime | None = None) -> None:
        self._runtime = runtime or SimulationRuntime()

    def simulate(self, req: MatchRequest) -> MatchResult:
        """Deterministic: identical (home, away, seed, rules) -> identical result."""
        return self._runtime.run(req)
