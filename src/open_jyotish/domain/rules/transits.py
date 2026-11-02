from __future__ import annotations

from open_jyotish.domain.models.chart_result import PlanetPosition
from open_jyotish.domain.models.chart_result import TransitEntry


RELATION_CANDIDATES = (
    (0.0, "Conjunction", 6.0),
    (60.0, "Sextile", 4.0),
    (90.0, "Square", 5.0),
    (120.0, "Trine", 5.0),
    (180.0, "Opposition", 6.0),
)

TRANSIT_PLANETS = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu", "Uranus", "Neptune", "Pluto"}


def build_transit_entries(
    *,
    natal_planets: list[PlanetPosition],
    transit_planets: list[PlanetPosition],
    natal_lagna_longitude: float,
) -> list[TransitEntry]:
    natal_map = {planet.planet: planet for planet in natal_planets}
    moon = natal_map.get("Moon")
    moon_sign_index = _sign_index(moon.longitude_sidereal) if moon is not None else _sign_index(natal_lagna_longitude)
    lagna_sign_index = _sign_index(natal_lagna_longitude)

    entries: list[TransitEntry] = []
    for transit in transit_planets:
        if transit.planet not in TRANSIT_PLANETS:
            continue
        natal = natal_map.get(transit.planet)
        if natal is None:
            continue
        transit_sign_index = _sign_index(transit.longitude_sidereal)
        natal_sign_index = _sign_index(natal.longitude_sidereal)
        relation_name, relation_orb = _relation_to_natal(
            transit_longitude=transit.longitude_sidereal,
            natal_longitude=natal.longitude_sidereal,
        )
        entries.append(
            TransitEntry(
                planet=transit.planet,
                natal_sign=natal.sign,
                transit_sign=transit.sign,
                transit_degree=transit.degree_in_sign,
                house_from_lagna=((transit_sign_index - lagna_sign_index) % 12) + 1,
                house_from_moon=((transit_sign_index - moon_sign_index) % 12) + 1,
                natal_house=natal.house,
                sign_shift=(transit_sign_index - natal_sign_index) % 12,
                relation_to_natal=relation_name,
                orb_degrees=relation_orb,
                retrograde=transit.retrograde,
                dignity=transit.dignity,
            )
        )
    return sorted(entries, key=lambda entry: _transit_sort_order(entry.planet))


def _transit_sort_order(planet_name: str) -> int:
    order = [
        "Saturn",
        "Jupiter",
        "Rahu",
        "Ketu",
        "Mars",
        "Sun",
        "Venus",
        "Mercury",
        "Moon",
        "Uranus",
        "Neptune",
        "Pluto",
    ]
    try:
        return order.index(planet_name)
    except ValueError:
        return 99


def _relation_to_natal(*, transit_longitude: float, natal_longitude: float) -> tuple[str, float | None]:
    difference = _normalize_degrees(transit_longitude - natal_longitude)
    best: tuple[float, str, float] | None = None
    for exact, label, max_orb in RELATION_CANDIDATES:
        distance = abs(difference - exact)
        distance = min(distance, 360.0 - distance)
        if distance > max_orb:
            continue
        if best is None or distance < best[0]:
            best = (distance, label, max_orb)
    if best is None:
        return "-", None
    return best[1], round(best[0], 2)


def _normalize_degrees(value: float) -> float:
    return value % 360.0


def _sign_index(longitude: float) -> int:
    return int(_normalize_degrees(longitude) // 30.0)

