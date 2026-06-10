"""Static pool of nation names (deterministic, index-stable for flavour only)."""
from __future__ import annotations

NATIONS: list[str] = [
    "Brazil", "Argentina", "France", "Germany", "Spain", "England", "Italy",
    "Netherlands", "Portugal", "Belgium", "Croatia", "Uruguay", "Mexico",
    "Colombia", "Denmark", "Switzerland", "United States", "Japan", "Senegal",
    "Morocco", "Poland", "Serbia", "South Korea", "Australia", "Canada",
    "Ghana", "Ecuador", "Cameroon", "Tunisia", "Nigeria", "Wales", "Qatar",
    "Sweden", "Norway", "Austria", "Turkey", "Egypt", "Chile", "Peru",
    "Iran", "Ivory Coast", "Algeria", "Scotland", "Greece", "Czechia",
    "Ukraine", "Costa Rica", "Paraguay",
]


def nation_name(index: int) -> str:
    return NATIONS[index] if index < len(NATIONS) else f"Nation {index + 1:02d}"
