"""Tournament rules: format, tiebreakers, extra-time/penalty resolution."""
from __future__ import annotations
from src.domain.match import MatchResult
from src.seed.provider import sub_seed


class TournamentPolicy:
    def __init__(self, master_seed: int) -> None:
        self._seed = master_seed

    def resolve_draw(self, result: MatchResult, match_id: str) -> MatchResult:
        """Deterministic penalty shootout when a knockout is still level."""
        # TODO: simulate penalties via SeededRng(sub_seed(seed,"pens",match_id)).
        return result
