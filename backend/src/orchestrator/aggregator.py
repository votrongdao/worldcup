"""ResultAggregator: collate stats, update ratings, optional commentary.

The worker owns the event log (it appends each match's events as it simulates), so
the aggregator does NOT re-append — that would double-count. Its job is post-match
enrichment: ratings (future) and optional, cache-keyed commentary via the LLM.
"""
from __future__ import annotations
from src.domain.match import MatchResult
from src.infra.ports import EventLog, LlmGateway


class ResultAggregator:
    def __init__(self, log: EventLog, llm: LlmGateway | None = None) -> None:
        self._log = log
        self._llm = llm

    async def ingest(self, result: MatchResult) -> None:
        # Event-log persistence happens in the worker; nothing to append here.
        # TODO: update Elo ratings; optionally request cached commentary via self._llm.
        return None
