"""Records MatchEvents and (optionally) frame summaries for live/replay."""
from __future__ import annotations
from src.domain.match import MatchEvent


class EventRecorder:
    def __init__(self) -> None: self._events: list[MatchEvent] = []
    def record(self, e: MatchEvent) -> None: self._events.append(e)
    def log(self) -> list[MatchEvent]: return self._events
