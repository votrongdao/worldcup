"""Formations and tactical styles (English) — ported from frontend/match.html.

Style parameter vectors are carried over verbatim from the reference simulation;
only the labels are translated to English (no Vietnamese strings ship). Generated
teams inherit a style from their StyleDNA via ``style_for_dna``.
"""
from __future__ import annotations
from dataclasses import dataclass

from src.domain.team import StyleDNA

# role, x-fraction (own goal = 0), y-fraction of pitch width
Slot = tuple[str, float, float]

FORMATIONS: dict[str, list[Slot]] = {
    "4-4-2": [("GK", .05, .5), ("DEF", .24, .16), ("DEF", .22, .38), ("DEF", .22, .62),
              ("DEF", .24, .84), ("MID", .5, .16), ("MID", .48, .4), ("MID", .48, .6),
              ("MID", .5, .84), ("FWD", .74, .4), ("FWD", .74, .6)],
    "4-3-3": [("GK", .05, .5), ("DEF", .24, .15), ("DEF", .22, .38), ("DEF", .22, .62),
              ("DEF", .24, .85), ("MID", .46, .3), ("MID", .44, .5), ("MID", .46, .7),
              ("FWD", .72, .18), ("FWD", .76, .5), ("FWD", .72, .82)],
    "4-2-3-1": [("GK", .05, .5), ("DEF", .24, .15), ("DEF", .22, .38), ("DEF", .22, .62),
                ("DEF", .24, .85), ("MID", .4, .38), ("MID", .4, .62), ("MID", .6, .22),
                ("MID", .62, .5), ("MID", .6, .78), ("FWD", .8, .5)],
    "3-5-2": [("GK", .05, .5), ("DEF", .24, .3), ("DEF", .22, .5), ("DEF", .24, .7),
              ("MID", .5, .1), ("MID", .46, .32), ("MID", .44, .5), ("MID", .46, .68),
              ("MID", .5, .9), ("FWD", .74, .42), ("FWD", .74, .58)],
    "5-3-2": [("GK", .05, .5), ("DEF", .22, .1), ("DEF", .24, .3), ("DEF", .22, .5),
              ("DEF", .24, .7), ("DEF", .22, .9), ("MID", .48, .3), ("MID", .46, .5),
              ("MID", .48, .7), ("FWD", .72, .42), ("FWD", .72, .58)],
    "3-4-3": [("GK", .05, .5), ("DEF", .24, .3), ("DEF", .22, .5), ("DEF", .24, .7),
              ("MID", .48, .14), ("MID", .46, .4), ("MID", .46, .6), ("MID", .48, .86),
              ("FWD", .74, .22), ("FWD", .78, .5), ("FWD", .74, .78)],
    "5-3-1": [("GK", .05, .5), ("DEF", .2, .1), ("DEF", .22, .3), ("DEF", .2, .5),
              ("DEF", .22, .7), ("DEF", .2, .9), ("MID", .44, .3), ("MID", .42, .5),
              ("MID", .44, .7), ("MID", .6, .5), ("FWD", .76, .5)],
}


@dataclass(frozen=True)
class TacticalStyle:
    line: float       # defensive line height (0 deep .. 1 high)
    press: float      # pressing intensity
    width: float      # how wide the team plays
    overlap: float    # full-back / wide overlap tendency
    possess: float    # possession bias (vs directness)
    pass_len: float   # preferred pass length (metres)
    compact: float    # defensive compactness
    counter: float    # counter-attack tendency
    tempo: float      # speed multiplier
    aggr: float       # foul/aggression tendency


STYLES: dict[str, TacticalStyle] = {
    "Overlap":           TacticalStyle(.42, .60, 1.25, .85, .55, 18, .50, .60, 1.03, .50),
    "Tiki-Taka":         TacticalStyle(.55, .82, 1.00, .50, .92, 10, .80, .45, 1.00, .40),
    "Total Football":    TacticalStyle(.62, .95, 1.20, .80, .80, 14, .55, .70, 1.07, .55),
    "Defensive":         TacticalStyle(.26, .40, 0.85, .20, .45, 16, .92, .40, 0.98, .55),
    "Counter-Attack":    TacticalStyle(.30, .50, 0.90, .35, .40, 24, .85, .95, 1.05, .50),
    "Possession Attack": TacticalStyle(.52, .75, 1.15, .60, .85, 12, .60, .55, 1.02, .45),
}

FORMATION_KEYS = list(FORMATIONS)
STYLE_KEYS = list(STYLES)

_DNA_STYLE: dict[StyleDNA, str] = {
    StyleDNA.POSSESSION: "Tiki-Taka",
    StyleDNA.HIGH_PRESS: "Total Football",
    StyleDNA.COUNTER: "Counter-Attack",
    StyleDNA.DIRECT: "Overlap",
    StyleDNA.BALANCED: "Possession Attack",
}


def style_for_dna(dna: StyleDNA) -> str:
    return _DNA_STYLE.get(dna, "Possession Attack")
