from __future__ import annotations

from datetime import datetime

from open_jyotish.domain.models.chart_result import PlanetPosition
from open_jyotish.domain.models.chart_result import PlanetStateProfile


SUPPORTED_STATE_PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")

ACTIVITY_SEQUENCE = (
    "Nidra (sleeping)",
    "Gamana (on the move)",
    "Aagamana (coming)",
    "NrityaLipsa (desirous of dancing)",
    "Netrapani (eyes and hands)",
    "Prakasha (shining)",
    "Bhojana (eating)",
    "Sabha (in assembly)",
)

MALEFIC_PLANETS = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}
BENEFIC_PLANETS = {"Moon", "Mercury", "Jupiter", "Venus"}


def compute_planetary_states(
    *,
    planets: list[PlanetPosition],
    birth_local: datetime | None,
) -> list[PlanetStateProfile]:
    planet_map = {planet.planet: planet for planet in planets if planet.planet in SUPPORTED_STATE_PLANETS}
    sun = planet_map.get("Sun")
    results: list[PlanetStateProfile] = []
    for planet_name in SUPPORTED_STATE_PLANETS:
        planet = planet_map.get(planet_name)
        if planet is None:
            continue
        results.append(
            PlanetStateProfile(
                planet=planet_name,
                age_state=compute_age_state(planet),
                alertness_state=compute_alertness_state(planet),
                mood_states=compute_mood_states(
                    planet=planet,
                    sun=sun,
                    birth_local=birth_local,
                ),
                activity_state=compute_activity_state(planet),
            )
        )
    return results


def compute_age_state(planet: PlanetPosition) -> str:
    degree = planet.degree_in_sign
    if degree < 6.0:
        return "Baala (infant)"
    if degree < 12.0:
        return "Kumara (adolescent)"
    if degree < 18.0:
        return "Yuva (young)"
    if degree < 24.0:
        return "Vriddha (old)"
    return "Mrita (dead)"


def compute_alertness_state(planet: PlanetPosition) -> str:
    if planet.planet == "Rahu":
        return "Jaagrita (awake)"
    if planet.planet == "Ketu":
        return "Sushupta (asleep)"
    if planet.dignity in {"Exalted", "Own Sign"} or planet.house in {1, 4, 7, 10}:
        return "Jaagrita (awake)"
    if planet.dignity == "Debilitated" or planet.house in {6, 8, 12}:
        return "Sushupta (asleep)"
    return "Swapna (dreaming)"


def compute_mood_states(
    *,
    planet: PlanetPosition,
    sun: PlanetPosition | None,
    birth_local: datetime | None,
) -> list[str]:
    moods: list[str] = []
    if planet.dignity in {"Exalted", "Own Sign"}:
        moods.append("Swastha (comfortable)")
    elif planet.dignity == "Debilitated":
        moods.append("Duhkhita (distressed)")
    elif planet.house in {1, 5, 9, 10}:
        moods.append("Mudita (delighted)")
    elif planet.house in {6, 8, 12}:
        moods.append("Duhkhita (distressed)")
    else:
        moods.append("Saanta (peaceful)")

    if planet.planet in {"Rahu", "Ketu"} or planet.house in {3, 6, 11}:
        moods.append("Khala (mischievous)")
    if planet.planet in {"Mercury", "Saturn"} and planet.house in {6, 8, 12}:
        moods.append("Vikala (crippled)")
    if planet.retrograde and planet.planet in MALEFIC_PLANETS:
        moods.append("Kopita (angry)")
    if sun is not None and planet.planet != "Sun":
        if angular_distance(planet.longitude_sidereal, sun.longitude_sidereal) <= 8.0:
            moods.append("Lajjita (ashamed)")
    if birth_local is not None and planet.planet in BENEFIC_PLANETS and birth_local.hour < 6:
        moods.append("Mudita (delighted)")
    return dedupe(moods)


def compute_activity_state(planet: PlanetPosition) -> str:
    bucket = int((planet.longitude_sidereal % 360.0) // 45.0)
    offset = SUPPORTED_STATE_PLANETS.index(planet.planet) % len(ACTIVITY_SEQUENCE)
    return ACTIVITY_SEQUENCE[(bucket + offset) % len(ACTIVITY_SEQUENCE)]


def angular_distance(left: float, right: float) -> float:
    delta = abs((left % 360.0) - (right % 360.0))
    return min(delta, 360.0 - delta)


def dedupe(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
