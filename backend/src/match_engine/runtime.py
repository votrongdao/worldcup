"""Fixed-timestep simulation loop. Pure function of the MatchRequest.

A match is simulated as a deterministic sequence of attacking phases driven
solely by ``SeededRng(req.seed)``: identical ``(home, away, seed, rules)`` always
yields an identical event log and score. Team strength is derived from the
starting XI attributes, the coach profile, and the team rating.

The per-player 2D physics / policy path (``physics.py``, ``team_orchestrator.py``,
the ``DecisionPolicy`` implementations) lands behind this same ``run()`` boundary
later; until then this high-level chance model is the authoritative, reproducible
engine. Nothing here reads a clock, ``random``, or any ambient source — every roll
comes from the seeded RNG, preserving the determinism invariant the run-hash checks.
"""
from __future__ import annotations
from dataclasses import dataclass

from src.domain.match import (
    MatchEvent,
    MatchEventType,
    MatchRequest,
    MatchResult,
    MatchStats,
)
from src.domain.player import Player, Role
from src.domain.team import Team
from src.seed.rng import SeededRng
from .recorder import EventRecorder
from .world import MatchWorldState

FIXED = 1.0 / 120.0          # physics substep, seconds (reserved for the body sim)
EXTRA_TIME = 30.0            # minutes added when a knockout tie is still level
_SHOOTOUT_ROUNDS = 5        # standard best-of-five before sudden death


@dataclass(frozen=True)
class _Strength:
    """Per-team scalars distilled from the XI, coach, and rating (all ~[0,1])."""

    attack: float
    defense: float
    keeping: float
    finishing: float


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return lo if x < lo else hi if x > hi else x


def _norm_rating(r: float) -> float:
    """Accept ratings on either a [0,1] or a [0,100] scale, normalize to [0,1]."""
    return _clamp(r / 100.0 if r > 1.0 else r)


def _starting_xi(team: Team) -> list[Player]:
    ids = set(team.xi)
    sel = [p for p in team.squad if p.id in ids]
    return sel if sel else team.squad[:11]


def _strength(team: Team) -> _Strength:
    xi = _starting_xi(team)
    outfield = [p for p in xi if p.role != Role.GK] or xi
    n = len(outfield)
    attack = sum(0.4 * p.shooting + 0.3 * p.passing + 0.2 * p.dribbling + 0.1 * p.pace
                 for p in outfield) / n
    defense = sum(0.7 * p.defending + 0.3 * p.teamwork for p in outfield) / n
    finishing = sum(p.shooting for p in outfield) / n
    gk = next((p for p in xi if p.role == Role.GK), None)
    keeping = gk.defending if gk is not None else defense

    c = team.coach
    attack *= (0.85 + 0.30 * c.aggression) * (0.90 + 0.20 * c.tempo)
    defense *= (0.90 + 0.20 * c.pressing)

    rating = _norm_rating(team.rating)
    attack = _clamp(0.70 * attack + 0.30 * rating)
    defense = _clamp(0.70 * defense + 0.30 * rating)
    return _Strength(attack=attack, defense=defense, keeping=keeping, finishing=finishing)


def _ev(t: float, type_: MatchEventType, team: str | None = None, **meta: object) -> MatchEvent:
    return MatchEvent(t=round(t, 3), type=type_, team=team, meta=dict(meta))


class SimulationRuntime:
    def __init__(self) -> None:
        # The body-level physics engine is reserved for the per-player path; the
        # high-level chance model below does not integrate forces.
        pass

    def run(self, req: MatchRequest) -> MatchResult:
        rng = SeededRng(req.seed)
        world = MatchWorldState()
        rec = EventRecorder()

        home = _strength(req.home)
        away = _strength(req.away)

        rec.record(_ev(0.0, MatchEventType.KICKOFF))

        # --- Regulation ---------------------------------------------------
        shots_home, shots_away, phases, poss_home = self._play(
            rng, world, rec, home, away, start=0.0, minutes=req.rules.duration)
        score_home, score_away = world.score
        rec.record(_ev(req.rules.duration, MatchEventType.FULLTIME,
                       score=[score_home, score_away]))

        decided_by: str = "regulation"
        clock = req.rules.duration

        # --- Extra time (knockouts only) ---------------------------------
        if score_home == score_away and req.rules.extra_time:
            rec.record(_ev(clock, MatchEventType.ET_START))
            et_home, et_away, et_phases, et_poss = self._play(
                rng, world, rec, home, away, start=clock, minutes=EXTRA_TIME)
            shots_home += et_home
            shots_away += et_away
            # Possession is a phase-weighted blend of regulation + extra time.
            total = phases + et_phases
            poss_home = (poss_home * phases + et_poss * et_phases) / total
            phases = total
            score_home, score_away = world.score
            clock += EXTRA_TIME
            if score_home != score_away:
                decided_by = "extra_time"

        # --- Penalty shootout --------------------------------------------
        if score_home == score_away and req.rules.penalties:
            ph, pa = self._shootout(rng, rec, home, away, clock)
            decided_by = "penalties"
            winner: str | None = "home" if ph > pa else "away"
        else:
            if score_home > score_away:
                winner = "home"
            elif score_away > score_home:
                winner = "away"
            else:
                winner = None  # a legal draw (e.g. group stage)

        rec.record(_ev(clock, MatchEventType.END))

        return MatchResult(
            match_id=req.match_id,
            score_home=score_home,
            score_away=score_away,
            decided_by=decided_by,  # type: ignore[arg-type]
            winner=winner,  # type: ignore[arg-type]
            events=rec.log(),
            stats=MatchStats(
                poss_home=round(poss_home, 3),
                shots_home=shots_home,
                shots_away=shots_away,
            ),
        )

    # ------------------------------------------------------------------ #
    def _play(
        self,
        rng: SeededRng,
        world: MatchWorldState,
        rec: EventRecorder,
        home: _Strength,
        away: _Strength,
        start: float,
        minutes: float,
    ) -> tuple[int, int, int, float]:
        """Resolve one attacking phase per simulated minute; mutate world.score.

        Returns ``(shots_home, shots_away, phases, poss_home)`` so the caller can
        accumulate stats across regulation + extra time.
        """
        shots_home = shots_away = 0
        home_phases = 0
        n = int(round(minutes))
        for i in range(n):
            t = start + i + 1  # phase resolves at the end of minute i (1-indexed)
            world.sim_time = t

            # Possession: the stronger midfield/attack keeps the ball more often.
            p_home = home.attack / (home.attack + away.attack) if (home.attack + away.attack) else 0.5
            home_has_ball = rng.random() < p_home
            if home_has_ball:
                home_phases += 1
                created = self._phase(rng, world, rec, home, away, side="home", t=t)
                shots_home += created
            else:
                created = self._phase(rng, world, rec, away, home, side="away", t=t)
                shots_away += created

        poss_home = home_phases / n if n else 0.5
        return shots_home, shots_away, n, poss_home

    def _phase(
        self,
        rng: SeededRng,
        world: MatchWorldState,
        rec: EventRecorder,
        atk: _Strength,
        dfn: _Strength,
        side: str,
        t: float,
    ) -> int:
        """One attack by ``atk`` against ``dfn``. Returns 1 if a shot was taken."""
        # Chance creation: base rate nudged by attack-minus-defense.
        shot_prob = _clamp(0.20 + 0.16 * (atk.attack - dfn.defense), 0.04, 0.45)
        if rng.random() >= shot_prob:
            return 0

        rec.record(_ev(t, MatchEventType.SHOT, team=side))
        # Conversion: finisher quality vs the keeper, with a finite floor/ceiling.
        goal_prob = _clamp(0.11 + 0.18 * (atk.finishing - dfn.keeping), 0.02, 0.45)
        if rng.random() < goal_prob:
            h, a = world.score
            world.score = (h + 1, a) if side == "home" else (h, a + 1)
            rec.record(_ev(t, MatchEventType.GOAL, team=side,
                           score=[world.score[0], world.score[1]]))
        else:
            rec.record(_ev(t, MatchEventType.SAVE, team=side))
        return 1

    def _shootout(
        self,
        rng: SeededRng,
        rec: EventRecorder,
        home: _Strength,
        away: _Strength,
        clock: float,
    ) -> tuple[int, int]:
        """Best-of-five then sudden death. Records PENALTY events; score unchanged."""
        h_conv = _clamp(0.78 + 0.20 * (home.finishing - away.keeping), 0.55, 0.97)
        a_conv = _clamp(0.78 + 0.20 * (away.finishing - home.keeping), 0.55, 0.97)
        h = a = 0
        for r in range(_SHOOTOUT_ROUNDS):
            if rng.random() < h_conv:
                h += 1
                rec.record(_ev(clock, MatchEventType.PENALTY, team="home", round=r + 1, scored=True))
            else:
                rec.record(_ev(clock, MatchEventType.PENALTY, team="home", round=r + 1, scored=False))
            if rng.random() < a_conv:
                a += 1
                rec.record(_ev(clock, MatchEventType.PENALTY, team="away", round=r + 1, scored=True))
            else:
                rec.record(_ev(clock, MatchEventType.PENALTY, team="away", round=r + 1, scored=False))

        r = _SHOOTOUT_ROUNDS
        while h == a:  # sudden death: paired kicks until one side leads
            r += 1
            sh = rng.random() < h_conv
            sa = rng.random() < a_conv
            if sh:
                h += 1
            if sa:
                a += 1
            rec.record(_ev(clock, MatchEventType.PENALTY, team="home", round=r, scored=sh))
            rec.record(_ev(clock, MatchEventType.PENALTY, team="away", round=r, scored=sa))
        return h, a
