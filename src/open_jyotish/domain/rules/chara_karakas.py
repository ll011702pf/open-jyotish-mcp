from __future__ import annotations

from open_jyotish.domain.models.chart_result import CharaKarakaAssignment
from open_jyotish.domain.models.chart_result import PlanetPosition


CHARA_KARAKA_ROLES = (
    ("AK", "Self"),
    ("AmK", "Minister"),
    ("BK", "Brother"),
    ("MK", "Mother"),
    ("PiK", "Father"),
    ("PK", "Children"),
    ("GK", "Conflicts"),
    ("DK", "Spouse"),
)

CHART_KARAKA_PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu")


def compute_chara_karakas(planets: list[PlanetPosition]) -> list[CharaKarakaAssignment]:
    eligible = [planet for planet in planets if planet.planet in CHART_KARAKA_PLANETS]
    ranking = sorted(
        eligible,
        key=lambda item: (karaka_rank_value(item), item.longitude_sidereal),
        reverse=True,
    )
    assignments: list[CharaKarakaAssignment] = []
    for (role, meaning), planet in zip(CHARA_KARAKA_ROLES, ranking, strict=False):
        assignments.append(
            CharaKarakaAssignment(
                role=role,
                planet=planet.planet,
                meaning=meaning,
                rank_value=round(karaka_rank_value(planet), 4),
            )
        )
    return assignments


def karaka_rank_value(planet: PlanetPosition) -> float:
    if planet.planet == "Rahu":
        return round(30.0 - planet.degree_in_sign, 6)
    return round(planet.degree_in_sign, 6)
