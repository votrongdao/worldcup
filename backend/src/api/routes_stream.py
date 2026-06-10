"""Live match streaming.

The cloud path uses Azure SignalR; locally we stream the deterministic engine's
frames over a WebSocket (the SignalR stand-in), paced in real time so a match can be
watched live. The same engine that produced the recorded scoreline is re-run with
frame capture, so the live view is always consistent with the result.
"""
from __future__ import annotations
import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.app.deps import get_deps
from src.domain.match import MatchRequest, MatchRules
from src.domain.tournament import Phase
from src.match_engine.engine import MatchEngine
from src.match_engine.tactics import style_for_dna
from src.seed.provider import sub_seed

router = APIRouter(tags=["stream"])
_engine = MatchEngine()

_MIN_PER_REALSEC = 2.6     # sim-minutes streamed per real second (~35 s per match)
_MAX_STEP = 0.4           # cap per-frame sleep so it never stalls


@router.post("/negotiate")
async def negotiate(tid: str, mid: str) -> dict:
    deps = get_deps()
    if deps.settings.backend.lower() == "azure":
        sr = deps.signalr
        if hasattr(sr, "negotiate"):
            return sr.negotiate(mid)  # type: ignore[attr-defined]
    return {"mode": "ws", "url": f"/api/ws/match/{tid}/{mid}"}


@router.websocket("/ws/match/{tid}/{mid}")
async def ws_match(ws: WebSocket, tid: str, mid: str) -> None:
    await ws.accept()
    deps = get_deps()
    try:
        t = await deps.store.load(tid)
    except Exception:
        await ws.close(code=1008)
        return
    summ = t.results.get(mid)
    home = t.teams.get(summ.home_id) if summ else None
    away = t.teams.get(summ.away_id) if summ else None
    if summ is None or home is None or away is None:
        await ws.close(code=1008)
        return

    knockout = summ.phase is not Phase.GROUP
    req = MatchRequest(
        match_id=mid, home=home, away=away,
        seed=sub_seed(t.config.seed, "match", mid),
        rules=MatchRules(duration=90.0, extra_time=knockout, penalties=knockout),
    )
    # Engine runs synchronously (~0.6 s) then we stream its frames paced in real time.
    result = await asyncio.to_thread(_engine.simulate, req, True)
    goals = sorted((e.t, e.team) for e in result.events if e.type.value == "goal")

    try:
        await ws.send_json({
            "type": "meta", "matchId": mid,
            "homeNation": home.nation, "awayNation": away.nation,
            "homeFormation": home.coach.formation.value, "awayFormation": away.coach.formation.value,
            "homeStyle": style_for_dna(home.style_dna), "awayStyle": style_for_dna(away.style_dna),
        })
        prev = 0.0
        for fr in result.frames:
            gap = (fr["t"] - prev) / _MIN_PER_REALSEC
            prev = fr["t"]
            if gap > 0:
                await asyncio.sleep(min(gap, _MAX_STEP))
            sh = sum(1 for gt, gs in goals if gt <= fr["t"] and gs == "home")
            sa = sum(1 for gt, gs in goals if gt <= fr["t"] and gs == "away")
            await ws.send_json({"type": "frame", "frame": fr, "clock": fr["t"],
                                "scoreHome": sh, "scoreAway": sa})
        await ws.send_json({"type": "end", "scoreHome": result.score_home,
                            "scoreAway": result.score_away, "decidedBy": result.decided_by})
    except WebSocketDisconnect:
        return
    except Exception:
        pass
    finally:
        try:
            await ws.close()
        except Exception:
            pass
