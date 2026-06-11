"""Post-match analysis: per-player ratings + skill/form strengths & weaknesses,
and a per-team report (strengths, weaknesses, key player).

Pure functions over the finished World — no randomness, fully reproducible.
"""
from __future__ import annotations

from src.domain.match import PlayerRating, TeamMatchReport
from .world import Player, TeamState, World

# runtime-attr -> human label, in the order shown
_ATTRS: list[tuple[str, str]] = [
    ("shooting", "Finishing"), ("passing", "Passing"), ("dribbling", "Dribbling"),
    ("pace", "Pace"), ("vision", "Vision"), ("defending", "Defending"),
    ("stamina_attr", "Stamina"), ("teamwork", "Teamwork"),
]


def _side(idx: int) -> str:
    return "home" if idx == 0 else "away"


def _minutes(p: Player, final_clock: float) -> int:
    end = p.min_off if p.min_off is not None else final_clock
    return max(0, round(end - p.min_on))


# a keeper is judged on a goalkeeping-relevant subset, not finishing/pace
_GK_ATTRS = [("defending", "Reflexes"), ("vision", "Positioning"),
             ("passing", "Distribution"), ("teamwork", "Command of area")]


def _skill_strengths(p: Player) -> tuple[list[str], list[str]]:
    attrs = _GK_ATTRS if p.role == "GK" else _ATTRS
    ranked = sorted(attrs, key=lambda a: getattr(p, a[0]), reverse=True)
    strengths = [lbl for key, lbl in ranked[:2] if getattr(p, key) >= 0.55]
    weaknesses = [lbl for key, lbl in ranked[-2:] if getattr(p, key) <= 0.5]
    return strengths, weaknesses


def _rating(p: Player, conceded: int, minutes: int) -> float:
    if minutes <= 0:
        return 6.0
    r = 6.0
    if p.role == "GK":
        r += p.saves_p * 0.25 - conceded * 0.45
    r += p.goals_p * 1.1 + p.assists_p * 0.7 + p.shots_p * 0.08
    if p.passes_att >= 5:
        r += (p.passes_cmp / p.passes_att - 0.72) * 2.2
    r += p.tackles_won * 0.12 - p.fouls_p * 0.10
    return round(min(10.0, max(4.0, r)), 1)


def _distance_km(p: Player) -> float:
    # the sim is time-compressed; scale + cap so the figure reads like a real match
    return round(min(13.0, p.distance / 1000.0 * 0.55), 2)


def _player_rating(p: Player, idx: int, conceded: int, final_clock: float) -> PlayerRating:
    minutes = _minutes(p, final_clock)
    strengths, weaknesses = _skill_strengths(p)
    # form-based overrides reflecting what actually happened this match
    if p.goals_p >= 1:
        strengths = ["Clinical finishing"] + [s for s in strengths if s != "Finishing"]
    if p.tackles_won >= 3 and "Ball-winning" not in strengths:
        strengths.append("Ball-winning")
    if p.role == "GK" and p.saves_p >= 3:
        strengths = ["Shot-stopping"] + strengths
    if p.fouls_p >= 3 and "Discipline" not in weaknesses:
        weaknesses.append("Discipline")
    return PlayerRating(
        player_id=p.pid, side=_side(p.team), role=p.role, shirt=p.shirt,
        rating=_rating(p, conceded, minutes), minutes=minutes,
        goals=p.goals_p, assists=p.assists_p, shots=p.shots_p,
        passes=p.passes_att,
        pass_pct=round(p.passes_cmp / p.passes_att, 2) if p.passes_att else 0.0,
        tackles=p.tackles_won, saves=p.saves_p, fouls=p.fouls_p,
        distance_km=_distance_km(p), stamina_end=round(p.stamina, 2),
        sub_on=round(p.min_on) if p.min_on > 0 else None,
        sub_off=round(p.min_off) if p.min_off is not None else None,
        strengths=strengths[:3], weaknesses=weaknesses[:3],
    )


def build_player_ratings(world: World, final_clock: float) -> list[PlayerRating]:
    ratings: list[PlayerRating] = []
    for t in world.teams:
        conceded = world.score[1 - t.idx]
        for i, p in enumerate(t.roster):
            if not p.played:
                continue
            ratings.append(_player_rating(p, i, conceded, final_clock))
    return ratings


def _team_strengths(t: TeamState) -> tuple[list[str], list[str]]:
    bodies = [p for p in t.roster if p.role != "GK"] or t.roster
    means = {lbl: sum(getattr(p, key) for p in bodies) / len(bodies) for key, lbl in _ATTRS}
    ranked = sorted(means.items(), key=lambda kv: kv[1], reverse=True)
    return [lbl for lbl, _ in ranked[:2]], [lbl for lbl, _ in ranked[-2:]]


def build_reports(world: World, ratings: list[PlayerRating], final_clock: float) -> list[TeamMatchReport]:
    reports: list[TeamMatchReport] = []
    for t in world.teams:
        side = _side(t.idx)
        strengths, weaknesses = _team_strengths(t)
        side_ratings = [r for r in ratings if r.side == side]
        key = max(side_ratings, key=lambda r: (r.rating, r.minutes), default=None)
        reports.append(TeamMatchReport(
            side=side, formation_end=t.form_key, style_end=t.style_key,
            strengths=strengths, weaknesses=weaknesses,
            key_player=key.player_id if key else None,
            key_player_rating=key.rating if key else 0.0,
        ))
    return reports
