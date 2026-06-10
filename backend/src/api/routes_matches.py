"""Match + replay endpoints."""
from __future__ import annotations
from fastapi import APIRouter, HTTPException

from src.app.deps import get_deps

router = APIRouter(prefix="/matches", tags=["matches"])


def _as_dict(e) -> dict:
    return e.model_dump() if hasattr(e, "model_dump") else e


@router.get("/{mid}/events")
async def get_events(mid: str) -> list[dict]:
    """Ordered event log for a match (drives the timeline / replay)."""
    events = await get_deps().log.read(mid)
    return [_as_dict(e) for e in events]


@router.get("/{mid}")
async def get_match(mid: str) -> dict:
    """Match summary derived from its event log (goals, shots, final score)."""
    events = [_as_dict(e) for e in await get_deps().log.read(mid)]
    home = sum(1 for e in events if e.get("type") == "goal" and e.get("team") == "home")
    away = sum(1 for e in events if e.get("type") == "goal" and e.get("team") == "away")
    return {"matchId": mid, "scoreHome": home, "scoreAway": away,
            "events": events}


@router.get("/{mid}/commentary")
async def get_commentary(mid: str) -> dict:
    """AI commentary for a match (Azure AI Foundry, cached by match id)."""
    deps = get_deps()
    events = [_as_dict(e) for e in await deps.log.read(mid)]
    if not events:
        raise HTTPException(status_code=404, detail=f"no events for match {mid}")

    goals = [e for e in events if e.get("type") == "goal"]
    home = sum(1 for e in goals if e.get("team") == "home")
    away = sum(1 for e in goals if e.get("team") == "away")
    timeline = ", ".join(f"{e.get('team')} scored at {round(float(e.get('t', 0)))}'"
                         for e in goals) or "no goals"
    prompt = (
        "You are a witty football commentator. In TWO short sentences, sum up a match "
        f"that finished {home}-{away} (home-away). Goal timeline: {timeline}. "
        "Refer only to 'the home side' and 'the away side' — do not invent names."
    )
    try:
        text = await deps.llm.complete(prompt, seed_key=f"commentary:{mid}")
    except Exception as e:  # never let a provider error break the page
        text = f"(commentary unavailable: {type(e).__name__})"
    return {
        "matchId": mid, "scoreHome": home, "scoreAway": away,
        "commentary": text or "(LLM disabled — set WC_LLM_ENABLED=true and restart)",
    }
