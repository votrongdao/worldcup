"""Match Engine facade. The only entry point workers call."""
from __future__ import annotations
from src.domain.match import MatchRequest, MatchResult
from .runtime import SimulationRuntime


class MatchEngine:
    def __init__(self, runtime: SimulationRuntime | None = None) -> None:
        self._runtime = runtime or SimulationRuntime()

    def simulate(self, req: MatchRequest, capture_frames: bool = False) -> MatchResult:
        """Deterministic: identical (home, away, seed, rules) -> identical result.

        ``capture_frames=True`` also records the pitch frame stream (for replay/live);
        the result is otherwise identical, so frames stay consistent with the score.
        """
        return self._runtime.run(req, capture_frames=capture_frames)
