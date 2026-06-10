"""AI narrative endpoints (Azure AI Foundry / gpt-5.4-nano), cached per entity."""
from __future__ import annotations
from fastapi import APIRouter, HTTPException

from src.app.deps import get_deps
from src.domain.player import Role
from src.domain.tournament import Tournament
from .schemas import AiTextDTO

router = APIRouter(prefix="/tournaments", tags=["ai"])


async def _load(tid: str) -> Tournament:
    try:
        return await get_deps().store.load(tid)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"tournament {tid} not found")


def _name(t: Tournament, team_id: str | None) -> str:
    if not team_id:
        return "TBD"
    tm = t.teams.get(team_id)
    return tm.nation if tm else team_id


async def _complete(prompt: str, seed_key: str) -> AiTextDTO:
    deps = get_deps()
    cache_key = f"llm:{seed_key}"
    cached = await deps.cache.get(cache_key)
    if cached:
        return AiTextDTO(text=cached, cached=True)
    try:
        text = await deps.llm.complete(prompt, seed_key=seed_key)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM error: {type(e).__name__}")
    if not text:
        return AiTextDTO(text="(AI disabled — set WC_LLM_ENABLED=true and restart)")
    return AiTextDTO(text=text)


@router.get("/{tid}/summary", response_model=AiTextDTO)
async def tournament_summary(tid: str):
    t = await _load(tid)
    if t.phase.value != "done":
        raise HTTPException(status_code=409, detail="tournament not finished yet")

    final = next((b for b in t.bracket if b.phase.value == "final"), None)
    champ = _name(t, t.champion_id)
    runner = _name(t, (final.home_id if final and final.winner_id == final.away_id
                       else final.away_id) if final else None)
    final_res = t.results.get(final.match_id) if final else None
    score = f"{final_res.score_home}-{final_res.score_away}" if final_res else "?"
    decided = final_res.decided_by.replace("_", " ") if final_res else "regulation"
    group_winners = ", ".join(
        f"{g} ({_name(t, table[0].team_id)})" for g, table in sorted(t.standings.items())
    )
    prompt = (
        "You are a football writer. In 3-4 vivid but concise sentences, recap a "
        f"simulated {t.config.teams}-team World Cup. Champions: {champ}, who beat "
        f"{runner} {score} in the final (decided in {decided}). "
        f"Group winners: {group_winners}. Do not invent statistics beyond these facts."
    )
    return await _complete(prompt, seed_key=f"summary:{tid}")


@router.get("/{tid}/teams/{team_id}/report", response_model=AiTextDTO)
async def team_report(tid: str, team_id: str):
    t = await _load(tid)
    tm = t.teams.get(team_id)
    if tm is None:
        raise HTTPException(status_code=404, detail=f"team {team_id} not found")

    xi_ids = set(tm.xi)
    xi = [p for p in tm.squad if p.id in xi_ids] or tm.squad[:11]

    def best(role: Role, attr: str) -> float:
        vals = [getattr(p, attr) for p in xi if p.role == role]
        return max(vals) if vals else 0.0

    c = tm.coach
    style = "high pressing" if c.pressing > 0.65 else "patient build-up"
    record = ""
    for table in t.standings.values():
        for s in table:
            if s.team_id == team_id:
                record = f"{s.w}W-{s.d}D-{s.l}L, {s.gf} for / {s.ga} against"
    prompt = (
        f"Write a 3-4 sentence scouting report for {tm.nation}, a tier-{tm.tier} side "
        f"playing {tm.style_dna.value} football in a {c.formation.value} under a "
        f"{style} coach. Squad signals: attacking threat {best(Role.FWD, 'shooting'):.2f}, "
        f"creativity {best(Role.MID, 'vision'):.2f}, defensive solidity "
        f"{best(Role.DEF, 'defending'):.2f} (0-1 scale). "
        + (f"Group-stage record: {record}. " if record else "")
        + "Be concrete about strengths and weaknesses; do not invent player names."
    )
    return await _complete(prompt, seed_key=f"report:{tid}:{team_id}")
