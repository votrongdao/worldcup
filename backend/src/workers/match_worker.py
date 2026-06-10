"""Consumes a queued MatchRequest, runs the deterministic engine, emits events/results."""
from __future__ import annotations
from src.domain.match import MatchRequest, MatchResult
from src.match_engine.engine import MatchEngine
from src.infra.ports import EventLog, ResultBus, SignalRPort

_engine = MatchEngine()


async def handle(req: MatchRequest, log: EventLog, bus: ResultBus,
                 signalr: SignalRPort | None = None) -> MatchResult:
    result = _engine.simulate(req)                 # pure / deterministic
    await log.append(req.match_id, result.events)  # append-only event log
    if req.render and signalr is not None:
        await signalr.push(req.match_id, {
            "type": "final", "score": [result.score_home, result.score_away],
        })
    await bus.publish(result)                       # hand back to the orchestrator
    return result
