"""Tournament rules: format, tiebreakers, extra-time/penalty resolution."""
from __future__ import annotations
from src.domain.match import MatchResult
from src.seed.provider import sub_seed
from src.seed.rng import SeededRng


class TournamentPolicy:
    def __init__(self, master_seed: int) -> None:
        self._seed = master_seed

    def resolve_draw(self, result: MatchResult, match_id: str) -> MatchResult:
        """Guarantee a decisive knockout result.

        The match engine already resolves draws via extra time + a penalty shootout
        when those rules are enabled, so this is the single, authoritative place that
        enforces "a knockout must have a winner". If a result somehow arrives level
        (e.g. an engine that did not run a shootout), a deterministic seeded lot
        decides it so the bracket can always advance.
        """
        if result.winner is not None:
            return result
        rng = SeededRng(sub_seed(self._seed, "pens", match_id))
        result.winner = "home" if rng.random() < 0.5 else "away"
        if result.decided_by == "regulation":
            result.decided_by = "penalties"
        return result
