"""Tournament lifecycle + read-model endpoints."""
from __future__ import annotations
from fastapi import APIRouter, BackgroundTasks, HTTPException

from src.app.deps import get_deps
from src.domain.match import MatchRequest, MatchRules
from src.domain.tournament import Phase, Tournament
from src.match_engine.engine import MatchEngine
from src.orchestrator.fsm import TournamentOrchestrator
from src.seed.provider import sub_seed

_engine = MatchEngine()
from .schemas import (
    BracketSlotDTO,
    CoachDTO,
    CreateTournamentRequest,
    CreateTournamentResponse,
    MatchSummaryDTO,
    PlayerDTO,
    StandingDTO,
    TeamDetailDTO,
    TeamSummaryDTO,
    TournamentStatus,
)

router = APIRouter(prefix="/tournaments", tags=["tournaments"])


async def _load(tid: str) -> Tournament:
    try:
        return await get_deps().store.load(tid)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"tournament {tid} not found")


async def _run(config) -> None:
    d = get_deps()
    orch = TournamentOrchestrator(d.queue, d.store, d.log, d.bus, d.llm,
                                  events=d.events, cache=d.cache)
    await orch.start(config)


@router.post("", status_code=202, response_model=CreateTournamentResponse)
async def create_tournament(req: CreateTournamentRequest, bg: BackgroundTasks):
    bg.add_task(_run, req.config)
    return CreateTournamentResponse(id=f"wc-{req.config.seed}")


@router.get("/{tid}", response_model=TournamentStatus)
async def get_status(tid: str):
    t = await _load(tid)
    return TournamentStatus(
        id=t.id, phase=t.phase, run_hash=t.run_hash, champion_id=t.champion_id,
        runner_up_id=t.runner_up_id, third_place_id=t.third_place_id,
        teams=len(t.teams), groups=len(t.standings),
    )


@router.get("/{tid}/activity")
async def get_activity(tid: str, limit: int = 200) -> list[dict]:
    """Live agentic event feed for a run (run_started, phase, match, run_finished)."""
    return await get_deps().events.history(tid, limit=limit)


@router.get("/{tid}/standings", response_model=dict[str, list[StandingDTO]])
async def get_standings(tid: str):
    t = await _load(tid)
    return {g: [StandingDTO(**s.model_dump()) for s in table]
            for g, table in t.standings.items()}


@router.get("/{tid}/bracket", response_model=list[BracketSlotDTO])
async def get_bracket(tid: str):
    t = await _load(tid)
    return [BracketSlotDTO(**slot.model_dump()) for slot in t.bracket]


@router.get("/{tid}/teams", response_model=list[TeamSummaryDTO])
async def get_teams(tid: str):
    t = await _load(tid)
    return [
        TeamSummaryDTO(
            id=tm.id, nation=tm.nation, tier=tm.tier, rating=tm.rating,
            style_dna=tm.style_dna.value, group=t.group_of.get(tm.id, ""),
        )
        for tm in t.teams.values()
    ]


@router.get("/{tid}/teams/{team_id}", response_model=TeamDetailDTO)
async def get_team_detail(tid: str, team_id: str):
    t = await _load(tid)
    tm = t.teams.get(team_id)
    if tm is None:
        raise HTTPException(status_code=404, detail=f"team {team_id} not found")
    return TeamDetailDTO(
        id=tm.id, nation=tm.nation, tier=tm.tier, rating=tm.rating,
        style_dna=tm.style_dna.value, group=t.group_of.get(tm.id, ""),
        xi=tm.xi, colors=tm.colors,
        coach=CoachDTO(
            formation=tm.coach.formation.value, aggression=tm.coach.aggression,
            line_height=tm.coach.line_height, tempo=tm.coach.tempo,
            pressing=tm.coach.pressing, directness=tm.coach.directness),
        squad=[PlayerDTO(role=p.role.value, **p.model_dump(exclude={"role", "mass"}))
               for p in tm.squad],
    )


@router.get("/{tid}/matches", response_model=list[MatchSummaryDTO])
async def get_matches(tid: str):
    t = await _load(tid)
    return [MatchSummaryDTO(**s.model_dump()) for s in t.results.values()]


@router.get("/{tid}/matches/{mid}/replay")
async def get_replay(tid: str, mid: str):
    """Re-run the deterministic engine WITH frame capture — frames are consistent with
    the recorded scoreline because the same seed/rules reproduce the same match."""
    t = await _load(tid)
    summ = t.results.get(mid)
    if summ is None:
        raise HTTPException(status_code=404, detail=f"match {mid} not found")
    home, away = t.teams.get(summ.home_id), t.teams.get(summ.away_id)
    if home is None or away is None:
        raise HTTPException(status_code=404, detail="teams not found")

    knockout = summ.phase is not Phase.GROUP
    req = MatchRequest(
        match_id=mid, home=home, away=away,
        seed=sub_seed(t.config.seed, "match", mid),
        rules=MatchRules(duration=90.0, extra_time=knockout, penalties=knockout),
    )
    result = _engine.simulate(req, capture_frames=True)
    duration = 120.0 if result.decided_by in ("extra_time", "penalties") else 90.0
    return {
        "matchId": mid, "homeId": summ.home_id, "awayId": summ.away_id,
        "homeNation": home.nation, "awayNation": away.nation,
        "scoreHome": result.score_home, "scoreAway": result.score_away,
        "decidedBy": result.decided_by,
        "homeColors": home.colors, "awayColors": away.colors,
        "duration": duration, "frames": result.frames,
    }


@router.post("/{tid}/pause")
async def pause(tid: str):
    # Snapshot/resume lives in RunSupervisor; cooperative pause is future work.
    raise HTTPException(status_code=501, detail="pause not implemented")


@router.post("/{tid}/resume")
async def resume(tid: str):
    raise HTTPException(status_code=501, detail="resume not implemented")
