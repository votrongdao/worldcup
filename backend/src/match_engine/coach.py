"""In-match AI coach: deterministic tactical decisions taken while the match runs.

Every ~11–18 sim-seconds each coach re-reads the game state (scoreline, red cards,
clock, fatigue) and may: change the tactical STYLE, change the FORMATION, or make a
SUBSTITUTION (fresh legs / attacking or defensive intent). All randomness comes from
the match SeededRng, so decisions are reproducible. Decisions are returned as plain
dicts; the runtime turns them into events + CoachDecision records.

Player skills drive who comes on: the best-rated, freshest bench player for the role
the situation calls for — so a good squad keeps a suitable outcome late in the game.
"""
from __future__ import annotations

from src.seed.rng import SeededRng
from .physics import FIELD_L, FIELD_W, PAD, clamp
from .tactics import FORMATIONS
from .world import Player, TeamState, World

FATIGUE_SUB_AT = 0.55          # sub a player whose stamina drops below this
SUB_WINDOW_MIN = 55.0          # coaches start using the bench around the hour mark
MAX_FORM_CHANGES = 3


def _dec(t: float, side: str, kind: str, summary: str, reason: str) -> dict:
    return {"t": round(t, 1), "side": side, "kind": kind, "summary": summary, "reason": reason}


def _side(t: TeamState) -> str:
    return "home" if t.idx == 0 else "away"


# --------------------------------------------------------------------------- style
def _choose_style(t: TeamState, men: int, opp: int, diff: int, late: bool, rng: SeededRng) -> str:
    if men < opp:
        return "Defensive"
    if men > opp:
        return "Possession Attack"
    if late and diff < 0:
        return "Total Football" if diff <= -2 else "Possession Attack"
    if late and diff > 0:
        return "Counter-Attack"
    return "Tiki-Taka" if rng.random() < 0.5 else "Possession Attack"


# ----------------------------------------------------------------------- formation
def _choose_formation(t: TeamState, men: int, opp: int, diff: int, late: bool) -> str:
    if men < opp:
        return "5-3-2"                       # a man down: shore it up
    if late and diff > 0:
        return "5-3-2"                       # protect a late lead
    if late and diff <= -2:
        return "3-4-3"                       # throw bodies forward
    if late and diff < 0:
        return "4-2-3-1"                     # chase with an extra attacker
    return t.form_key


def _reslot(t: TeamState, new_form: str) -> None:
    """Re-tag the 11 on-pitch bodies onto the new formation's slots (index-aligned:
    slot 0 is GK in every formation, so the keeper stays the keeper). Players drift
    to the new shape via normal steering — no teleport."""
    slots = FORMATIONS[new_form]
    for p, (role, fx, fy) in zip(t.players, slots):
        if p.role == "GK":
            continue
        p.role, p.fx, p.fy = role, fx, fy


# --------------------------------------------------------------------- substitution
def _clear_ball_refs(world: World, gone: Player) -> None:
    b = world.ball
    if b.carrier is gone:
        b.carrier = None
    if b.last_kick is gone:
        b.last_kick = None
    if b.intended is gone:
        b.intended = None
    if b.last_passer is gone:
        b.last_passer = None
    if b.offside_mark and b.offside_mark.get("recv") is gone:
        b.offside_mark = None


def _bring_on(world: World, t: TeamState, outgoing: Player, incoming: Player, clock: float) -> None:
    t.bench.remove(incoming)
    incoming.team = t.idx
    incoming.dir = t.dir
    incoming.role, incoming.fx, incoming.fy = outgoing.role, outgoing.fx, outgoing.fy
    incoming.x, incoming.y = outgoing.x, outgoing.y
    incoming.vx = incoming.vy = 0.0
    incoming.tx, incoming.ty = outgoing.tx, outgoing.ty
    incoming.stamina = 1.0
    incoming.min_on = clock
    incoming.played = True
    incoming.action = None
    incoming.dec_t = 0.0
    outgoing.min_off = clock
    _clear_ball_refs(world, outgoing)
    idx = t.players.index(outgoing)
    t.players[idx] = incoming


def _best_bench(t: TeamState, role: str | None) -> Player | None:
    pool = [p for p in t.bench if p.role != "GK"]
    if not pool:
        return None
    if role:
        same = [p for p in pool if p.role == role]
        if same:
            pool = same
    # strongest, freshest; deterministic tie-break on shirt number
    return sorted(pool, key=lambda p: (-p.overall, -p.stamina, p.shirt))[0]


def _try_sub(world: World, t: TeamState, diff: int, late: bool, clock: float) -> dict | None:
    outfield = [p for p in world.active(t) if p.role != "GK"]
    if not outfield:
        return None
    defs = [p for p in outfield if p.role == "DEF"]
    fwds = [p for p in outfield if p.role == "FWD"]
    tired = min(outfield, key=lambda p: (p.stamina, p.shirt))

    outgoing: Player | None = None
    need: str | None = None
    reason = ""

    if late and diff < 0 and len(defs) >= 4 and any(p.role == "FWD" for p in t.bench):
        outgoing = min(defs, key=lambda p: (p.overall, p.shirt))     # drop a defender
        need, reason = "FWD", "chasing the game — extra attacker"
    elif late and diff > 0 and len(fwds) >= 2 and any(p.role == "DEF" for p in t.bench):
        outgoing = min(fwds, key=lambda p: (p.overall, p.shirt))     # drop a forward
        need, reason = "DEF", "protecting the lead — extra defender"
    elif tired.stamina < FATIGUE_SUB_AT:
        outgoing, need, reason = tired, tired.role, "tiring legs — fresh energy"
    else:
        return None

    incoming = _best_bench(t, need)
    if incoming is None:
        return None

    _bring_on(world, t, outgoing, incoming, clock)
    t.subs_left -= 1
    summary = f"#{outgoing.shirt} {outgoing.role} → #{incoming.shirt} {incoming.role}"
    return _dec(clock, _side(t), "substitution", summary, reason)


# --------------------------------------------------------------------------- tick
def coach_tick(world: World, rng: SeededRng, dt: float) -> list[dict]:
    """Advance each coach's decision timer; return any decisions taken this step."""
    out: list[dict] = []
    for t in world.teams:
        t.coach_t -= dt
        if t.coach_t > 0:
            continue
        t.coach_t = rng.uniform(11, 18)
        opp = world.teams[1 - t.idx]
        men, opp_men = len(world.active(t)), len(world.active(opp))
        diff = world.score[t.idx] - world.score[1 - t.idx]
        clock = world.clock
        late = clock > 70

        new_style = _choose_style(t, men, opp_men, diff, late, rng)
        if new_style != t.style_key:
            t.style_key = new_style
            t.style_changes += 1
            out.append(_dec(clock, _side(t), "tactic", f"Go {new_style}",
                            _style_reason(men, opp_men, diff, late)))

        new_form = _choose_formation(t, men, opp_men, diff, late)
        if new_form != t.form_key and t.form_changes < MAX_FORM_CHANGES:
            _reslot(t, new_form)
            old = t.form_key
            t.form_key = new_form
            t.form_changes += 1
            out.append(_dec(clock, _side(t), "formation", f"{old} → {new_form}",
                            _form_reason(men, opp_men, diff, late)))

        if t.subs_left > 0 and clock >= SUB_WINDOW_MIN and t.bench:
            sub = _try_sub(world, t, diff, late, clock)
            if sub:
                out.append(sub)
    return out


def _style_reason(men: int, opp: int, diff: int, late: bool) -> str:
    if men < opp:
        return "down to ten — sit deeper"
    if late and diff < 0:
        return "behind late — commit forward"
    if late and diff > 0:
        return "ahead late — hit on the break"
    return "control the tempo"


def _form_reason(men: int, opp: int, diff: int, late: bool) -> str:
    if men < opp:
        return "a man light — add a defender"
    if late and diff > 0:
        return "see out the win"
    if late and diff <= -2:
        return "all-out attack"
    return "need a goal — extra attacker"
