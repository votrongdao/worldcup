"""Deterministic 2D match simulation (ported from frontend/match.html, headless).

Replaces the earlier chance model: one seeded run produces the score, the event log,
and (optionally) the frame stream from real physics + two team AIs. Pure function of
the MatchRequest — identical (home, away, seed, rules) → identical everything.
"""
from __future__ import annotations
from dataclasses import dataclass

from src.domain.match import (
    CoachDecision, MatchEvent, MatchEventType, MatchRequest, MatchResult, MatchStats,
)
from src.domain.team import Team
from src.seed.rng import SeededRng
from . import behaviors as B
from . import coach
from .match_report import build_player_ratings, build_reports
from .physics import (
    BOX_D, BOX_W, FIELD_L, FIELD_W, GOAL_W, PAD, PEN_SPOT, clamp, dist,
    step_ball, step_players,
)
from .tactics import FORMATIONS, style_for_dna
from .world import Ball, Player, TeamState, World

_KIND_EVENT = {
    "tactic": MatchEventType.TACTIC_CHANGE,
    "formation": MatchEventType.FORMATION_CHANGE,
    "substitution": MatchEventType.SUBSTITUTION,
}
BENCH_MAX = 7          # bodies on the bench (subs are limited to subs_left)

DT = 0.05                      # 20 Hz physics
STEPS_PER_HALF = 1600          # 80 sim-seconds per half
ET_STEPS_PER_HALF = 540
FRAME_EVERY = 12               # sample a frame every ~0.6 s


# --------------------------------------------------------------------------- #
def _runtime_player(gp, team: int, dir_: int, role: str, fx: float, fy: float,
                    shirt: int, coach_aggr: float, played: bool) -> Player:
    is_gk = role == "GK"
    return Player(
        team=team, dir=dir_, role=role, fx=fx, fy=fy, pid=gp.id, shirt=shirt,
        max_v=5.4 if is_gk else 6.7 + gp.pace * 1.4,
        accel=26.0 if is_gk else 28.0 + gp.accel * 6.0,
        skill=(gp.passing + gp.dribbling + gp.defending + gp.vision) / 4.0,
        aggr=clamp(0.35 + coach_aggr * 0.3 + (1 - gp.teamwork) * 0.2, 0.2, 0.85),
        shooting=gp.shooting, passing=gp.passing,
        pace=gp.pace, dribbling=gp.dribbling, vision=gp.vision, defending=gp.defending,
        stamina_attr=gp.stamina, teamwork=gp.teamwork,
        overall=(gp.shooting + gp.passing + gp.dribbling + gp.pace + gp.vision
                 + gp.defending + gp.stamina + gp.teamwork) / 8.0,
        played=played,
    )


def _build_team(team: Team, idx: int) -> TeamState:
    dir_ = +1 if idx == 0 else -1
    form_key = team.coach.formation.value if team.coach.formation.value in FORMATIONS else "4-3-3"
    slots = FORMATIONS[form_key]
    by_id = {p.id: p for p in team.squad}
    xi = [by_id[i] for i in team.xi if i in by_id][:11] or team.squad[:11]
    n = min(11, len(xi))
    players = [_runtime_player(xi[i], idx, dir_, slots[i][0], slots[i][1], slots[i][2],
                               i + 1, team.coach.aggression, True)
               for i in range(n)]
    # bench: squad members not in the XI, parked off-pitch until subbed on.
    on = {p.id for p in xi[:n]}
    spare = [p for p in team.squad if p.id not in on][:BENCH_MAX]
    bench = [_runtime_player(gp, idx, dir_, gp.role.value, 0.5, 0.5,
                             n + 1 + k, team.coach.aggression, False)
             for k, gp in enumerate(spare)]
    return TeamState(
        idx=idx, dir=dir_, form_key=form_key, style_key=style_for_dna(team.style_dna),
        players=players, coach_t=0.0, name=team.nation,
        goal_x=FIELD_L if dir_ > 0 else 0.0, own_goal_x=0.0 if dir_ > 0 else FIELD_L,
        bench=bench, roster=players + bench, subs_left=5,
    )


def _formation_reset(world: World, kickoff_team: int) -> None:
    for t in world.teams:
        st = B.style_of(t)
        for p in t.players:
            if p.sent_off:
                continue
            x, y = B.formation_xy(p, st)
            x = clamp(x, PAD, FIELD_L - PAD)
            if t.dir > 0:
                x = min(x, FIELD_L / 2 - (2 if p.role == "FWD" else 6))
            else:
                x = max(x, FIELD_L / 2 + (2 if p.role == "FWD" else 6))
            p.x, p.y = x, clamp(y, PAD, FIELD_W - PAD)
            p.vx = p.vy = 0.0
            p.action = None
            p.dec_t = 0.0
    b = world.ball
    b.x, b.y, b.vx, b.vy = FIELD_L / 2, FIELD_W / 2, 0.0, 0.0
    b.carrier = None
    b.kick_lock = 0.0
    b.last_kick = None
    b.intended = None
    b.offside_mark = None
    world.state = "kickoff"
    world.state_t = 0.6
    world.dead_ball = {"team": kickoff_team, "type": "kickoff"}


def _set_dead_ball(world: World, team: int, type_: str, x: float, y: float) -> None:
    world.state = "dead"
    world.state_t = 1.0 if type_ == "penalty" else 0.7
    world.dead_ball = {"team": team, "type": type_, "x": x, "y": y}
    b = world.ball
    b.x, b.y, b.vx, b.vy = x, y, 0.0, 0.0
    b.carrier = None
    b.offside_mark = None
    b.kick_lock = 0.0


def _resume_kick(world: World, t: TeamState, x: float, y: float) -> None:
    world.state = "play"
    taker, bd = None, 1e9
    for p in world.active(t):
        if p.role == "GK":
            continue
        d = dist(p.x, p.y, x, y)
        if d < bd:
            bd, taker = d, p
    b = world.ball
    if taker is not None:
        taker.x, taker.y = x - t.dir * 1.0, y
    b.x, b.y, b.vx, b.vy = x, y, 0.0, 0.0
    b.carrier = taker
    b.kick_lock = 0.0
    world.last_touch_team = t.idx


def _take_penalty(world: World, rng: SeededRng, t: TeamState) -> None:
    world.state = "play"
    gy = FIELD_W / 2 + rng.uniform(-GOAL_W * 0.6, GOAL_W * 0.6)
    b = world.ball
    dx, dy = t.goal_x - b.x, gy - b.y
    d = (dx * dx + dy * dy) ** 0.5 or 1.0
    b.vx, b.vy = dx / d * 30, dy / d * 30
    b.carrier = None
    b.kick_lock = 0.2
    world.last_touch_team = t.idx


def _dead_ball_ai(world: World, rng: SeededRng) -> None:
    world.state_t -= DT
    for t in world.teams:
        st = B.style_of(t)
        for p in world.active(t):
            if p.role == "GK":
                B.set_target(p, t.own_goal_x + t.dir * 2.2,
                             clamp(world.ball.y, FIELD_W / 2 - GOAL_W, FIELD_W / 2 + GOAL_W), p.max_v)
            else:
                bx, by = B.formation_xy(p, st)
                B.set_target(p, bx, by, p.max_v * 0.85)
    if world.state_t <= 0:
        db = world.dead_ball
        t = world.teams[db["team"]]
        if db["type"] == "penalty":
            _take_penalty(world, rng, t)
        elif db["type"] == "kickoff":
            _resume_kick(world, t, FIELD_L / 2, FIELD_W / 2)
        else:
            _resume_kick(world, t, db["x"], db["y"])


def _send_off(p: Player) -> None:
    p.sent_off = True


def _commit_foul(world: World, rng: SeededRng, fouler: Player, victim: Player) -> None:
    fouler.fouls_p += 1
    in_box = ((fouler.x < BOX_D if fouler.team == 0 else fouler.x > FIELD_L - BOX_D)
              and abs(fouler.y - FIELD_W / 2) < BOX_W / 2)
    awarded = 1 - fouler.team
    roll = rng.random()
    if roll < 0.04:
        _send_off(fouler)
    elif roll < 0.32:
        fouler.yellow += 1
        if fouler.yellow >= 2:
            _send_off(fouler)
    if in_box:
        spot = PEN_SPOT if fouler.team == 0 else FIELD_L - PEN_SPOT
        _set_dead_ball(world, awarded, "penalty", spot, FIELD_W / 2)
    else:
        _set_dead_ball(world, awarded, "free",
                       clamp(victim.x, PAD + 2, FIELD_L - PAD - 2),
                       clamp(victim.y, PAD + 2, FIELD_W - PAD - 2))


def _update_control(world: World, rng: SeededRng) -> None:
    if world.state != "play":
        return
    b = world.ball
    if b.kick_lock > 0:
        b.kick_lock -= DT
    if b.carrier and b.carrier.sent_off:
        b.carrier = None

    # GK smother: a carrier dribbling into the box is closed down by the keeper.
    if b.carrier is not None:
        atk = b.carrier
        defend = world.teams[1 - atk.team]
        atk_goal_x = world.teams[atk.team].goal_x
        if dist(b.x, b.y, atk_goal_x, FIELD_W / 2) < 11:
            gk = next((p for p in world.active(defend) if p.role == "GK"), None)
            if gk is not None and dist(gk.x, gk.y, b.x, b.y) < 2.4 + gk.skill * 1.4:
                b.carrier = gk
                b.kick_lock = 0.15
                b.last_kick = gk
                b.vx = b.vy = 0.0
                world.last_touch_team = gk.team
                return

    if b.carrier is not None:
        carrier = b.carrier
        for d in world.active(world.teams[1 - carrier.team]):
            if d.role == "GK" or d.tackle_cool > 0:
                continue
            if dist(d.x, d.y, b.x, b.y) < B.TACKLE_R:
                d.tackle_cool = 0.55
                if rng.random() < (0.40 + d.skill * 0.35 - carrier.skill * 0.30):
                    d.tackles_won += 1
                    b.carrier = None
                    b.kick_lock = 0.10
                    b.last_kick = carrier
                    nd = dist(d.x, d.y, b.x, b.y) or 1
                    b.vx, b.vy = (d.x - b.x) / nd * 5, (d.y - b.y) / nd * 5
                    b.offside_mark = None
                else:
                    st = B.style_of(world.teams[d.team])
                    foul_p = 0.30 + d.aggr * 0.35 + st.aggr * 0.3 - d.skill * 0.2
                    if rng.random() < foul_p:
                        _commit_foul(world, rng, d, carrier)
                        return
                break

    if b.carrier is None:
        best, bd = None, B.CONTROL_R
        for t in world.teams:
            for p in world.active(t):
                if b.kick_lock > 0 and p is b.last_kick:
                    continue
                d = dist(p.x, p.y, b.x, b.y)
                if d < bd:
                    bd, best = d, p
        if best is not None:
            if b.offside_mark and best is b.offside_mark["recv"]:
                awarded = 1 - best.team
                b.carrier = None
                b.offside_mark = None
                _set_dead_ball(world, awarded, "free",
                               clamp(best.x, PAD + 2, FIELD_L - PAD - 2),
                               clamp(best.y, PAD + 2, FIELD_W - PAD - 2))
                return
            b.offside_mark = None
            # completed pass: the intended receiver (same team) gained control.
            if (b.intended is best and b.last_passer is not None
                    and b.last_passer.team == best.team and b.last_passer is not best):
                b.last_passer.passes_cmp += 1
            b.intended = None
            b.last_passer = None
            b.carrier = best
            world.last_touch_team = best.team
            best.dec_t = 0.0
            best.action = None
            b.vx *= 0.2
            b.vy *= 0.2


def _track_condition(world: World, real_s: float, dt_min: float) -> None:
    """Accumulate distance covered and deplete stamina (slower legs when tired).
    Higher stamina attribute → slower depletion; subs come on fresh (stamina 1.0)."""
    for t in world.teams:
        for p in world.active(t):
            sp = (p.vx * p.vx + p.vy * p.vy) ** 0.5
            p.distance += sp * real_s
            load = 0.0035 + 0.004 * (sp / (p.max_v or 1.0))
            p.stamina = max(0.25, p.stamina - dt_min * load / (0.45 + p.stamina_attr))


@dataclass
class _Acc:
    events: list
    frames: list
    capture: bool
    decisions: list  # CoachDecision records (also mirrored as timeline events)


class SimulationRuntime:
    def run(self, req: MatchRequest, capture_frames: bool = False) -> MatchResult:
        rng = SeededRng(req.seed)
        world = World(
            teams=[_build_team(req.home, 0), _build_team(req.away, 1)],
            ball=Ball(),
        )
        acc = _Acc(events=[], frames=[], capture=capture_frames, decisions=[])
        kickoff = 0 if rng.random() < 0.5 else 1
        _formation_reset(world, kickoff)
        acc.events.append(MatchEvent(t=0.0, type=MatchEventType.KICKOFF))

        dur = req.rules.duration
        self._half(world, rng, acc, 0.0, dur / 2, STEPS_PER_HALF)
        self._switch(world)
        self._half(world, rng, acc, dur / 2, dur, STEPS_PER_HALF, kickoff=1 - kickoff)
        acc.events.append(MatchEvent(t=dur, type=MatchEventType.FULLTIME,
                                     meta={"score": list(world.score)}))

        decided_by = "regulation"
        clock = dur
        if world.score[0] == world.score[1] and req.rules.extra_time:
            acc.events.append(MatchEvent(t=clock, type=MatchEventType.ET_START))
            self._half(world, rng, acc, clock, clock + 15, ET_STEPS_PER_HALF, kickoff=0)
            self._switch(world)
            self._half(world, rng, acc, clock + 15, clock + 30, ET_STEPS_PER_HALF, kickoff=1)
            clock += 30
            if world.score[0] != world.score[1]:
                decided_by = "extra_time"

        winner = "home" if world.score[0] > world.score[1] else "away" if world.score[1] > world.score[0] else None
        if world.score[0] == world.score[1] and req.rules.penalties:
            ph, pa = self._shootout(req, world, rng, acc, clock)
            decided_by = "penalties"
            winner = "home" if ph > pa else "away"

        tot_poss = world.poss[0] + world.poss[1] or 1
        fair = [sum(p.yellow + (3 if p.sent_off else 0) for p in t.players)
                for t in world.teams]

        ratings = build_player_ratings(world, clock)
        reports = build_reports(world, ratings, clock)
        # Mirror the analysis into the event log (one event) so the API can serve it.
        acc.events.append(MatchEvent(
            t=clock, type=MatchEventType.REPORT,
            meta={"ratings": [r.model_dump() for r in ratings],
                  "reports": [r.model_dump() for r in reports],
                  "decisions": [d.model_dump() for d in acc.decisions]}))

        result = MatchResult(
            match_id=req.match_id, score_home=world.score[0], score_away=world.score[1],
            decided_by=decided_by, winner=winner, events=acc.events,
            stats=MatchStats(poss_home=round(world.poss[0] / tot_poss, 3),
                             shots_home=world.shots[0], shots_away=world.shots[1],
                             fairplay_home=fair[0], fairplay_away=fair[1]),
            player_ratings=ratings, coach_decisions=acc.decisions, reports=reports,
        )
        if capture_frames:
            result.frames = acc.frames  # type: ignore[attr-defined]
        return result

    # ------------------------------------------------------------------ #
    def _switch(self, world: World) -> None:
        for t in world.teams:
            t.dir *= -1
            t.goal_x = FIELD_L if t.dir > 0 else 0.0
            t.own_goal_x = 0.0 if t.dir > 0 else FIELD_L
        world.half = 2 if world.half == 1 else world.half

    def _half(self, world: World, rng: SeededRng, acc: _Acc, min0: float, min1: float,
              steps: int, kickoff: int = 0) -> None:
        if min0 > 0:
            _formation_reset(world, kickoff)
        dt_min = (min1 - min0) / steps          # game-minutes per physics step
        real_s = dt_min * 60.0                  # for distance accounting
        for i in range(steps):
            world.clock = min0 + (min1 - min0) * i / steps
            world.state_t -= DT if world.state == "kickoff" else 0.0
            if world.state == "kickoff" and world.state_t <= 0:
                _resume_kick(world, world.teams[world.dead_ball["team"]], FIELD_L / 2, FIELD_W / 2)

            prev_score = list(world.score)
            prev_shots = list(world.shots)

            B.ai_step(world, rng, DT)
            step_players(world, DT)
            _track_condition(world, real_s, dt_min)
            if world.state == "play":
                ev = step_ball(world, DT)
                if ev == "goal_home":
                    self._goal(world, 0)
                elif ev == "goal_away":
                    self._goal(world, 1)
                elif ev == "save":
                    side = "home" if world.last_touch_team == 0 else "away"
                    gk = world.ball.carrier
                    if gk is not None and gk.role == "GK":
                        gk.saves_p += 1
                    acc.events.append(MatchEvent(t=round(world.clock, 1),
                                                 type=MatchEventType.SAVE, team=side))
                elif ev in ("out_left", "out_right"):
                    defi = 0 if ev == "out_left" else 1
                    t = world.teams[defi]
                    _set_dead_ball(world, defi, "free", t.own_goal_x + t.dir * 8,
                                   clamp(world.ball.y, PAD + 4, FIELD_W - PAD - 4))
                _update_control(world, rng)
            else:
                _dead_ball_ai(world, rng)

            for d in coach.coach_tick(world, rng, DT):
                acc.decisions.append(CoachDecision(**d))
                acc.events.append(MatchEvent(
                    t=d["t"], type=_KIND_EVENT[d["kind"]], team=d["side"],
                    meta={"summary": d["summary"], "reason": d["reason"]}))

            if world.ball.carrier is not None:
                world.poss[world.ball.carrier.team] += 1

            if world.score != prev_score:
                side = "home" if world.score[0] > prev_score[0] else "away"
                acc.events.append(MatchEvent(t=round(world.clock, 1), type=MatchEventType.GOAL,
                                             team=side, meta={"score": list(world.score)}))
            for side_i, side in ((0, "home"), (1, "away")):
                for _ in range(world.shots[side_i] - prev_shots[side_i]):
                    acc.events.append(MatchEvent(t=round(world.clock, 1), type=MatchEventType.SHOT, team=side))

            if acc.capture and i % FRAME_EVERY == 0:
                acc.frames.append(self._frame(world))

    def _goal(self, world: World, scorer: int) -> None:
        # credit the scorer (last player to strike) and assist (last intentional passer)
        b = world.ball
        striker = b.last_kick
        if striker is not None and striker.team == scorer:
            striker.goals_p += 1
            passer = b.last_passer
            if passer is not None and passer.team == scorer and passer is not striker:
                passer.assists_p += 1
        world.score[scorer] += 1
        _formation_reset(world, 1 - scorer)

    def _shootout(self, req, world, rng, acc, clock):
        h = B.style_of(world.teams[0])  # noqa: F841 (kept for symmetry)
        hk = sum(p.shooting for p in world.teams[0].players) / max(1, len(world.teams[0].players))
        ak = sum(p.shooting for p in world.teams[1].players) / max(1, len(world.teams[1].players))
        h_conv = clamp(0.78 + 0.18 * (hk - 0.6), 0.55, 0.95)
        a_conv = clamp(0.78 + 0.18 * (ak - 0.6), 0.55, 0.95)
        ph = pa = 0
        for r in range(5):
            if rng.random() < h_conv:
                ph += 1
            if rng.random() < a_conv:
                pa += 1
            acc.events.append(MatchEvent(t=clock, type=MatchEventType.PENALTY, team="home", meta={"round": r + 1}))
            acc.events.append(MatchEvent(t=clock, type=MatchEventType.PENALTY, team="away", meta={"round": r + 1}))
        r = 5
        while ph == pa:
            r += 1
            sh = rng.random() < h_conv
            sa = rng.random() < a_conv
            ph += 1 if sh else 0
            pa += 1 if sa else 0
        return ph, pa

    def _frame(self, world: World) -> dict:
        players = [[round(p.x, 2), round(p.y, 2)] for p in world.teams[0].players] + \
                  [[round(p.x, 2), round(p.y, 2)] for p in world.teams[1].players]
        return {"t": round(world.clock, 2), "players": players,
                "ball": [round(world.ball.x, 2), round(world.ball.y, 2)]}
