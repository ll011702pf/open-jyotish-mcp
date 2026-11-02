from __future__ import annotations

from open_jyotish.domain.models.chart_result import ArgalaEntry
from open_jyotish.domain.models.chart_result import PlanetPosition
from open_jyotish.domain.rules.strengths import normalize_degrees


PRIMARY_ARGALA_HOUSES = {2: 12, 4: 10, 11: 3}
SECONDARY_ARGALA_HOUSES = {5: 9, 8: 6}
ARGALA_PLANETS = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"}


def build_argala_entries(
    *,
    planets: list[PlanetPosition],
    lagna_longitude: float,
    auxiliary_points: list[PlanetPosition] | None = None,
) -> list[ArgalaEntry]:
    references = {"Lagna": normalize_degrees(lagna_longitude)}
    moon = next((planet for planet in planets if planet.planet == "Moon"), None)
    if moon is not None:
        references["Moon"] = moon.longitude_sidereal
    if auxiliary_points:
        al = next((point for point in auxiliary_points if point.planet == "AL"), None)
        if al is not None:
            references["AL"] = al.longitude_sidereal

    entries: list[ArgalaEntry] = []
    considered_planets = [planet for planet in planets if planet.planet in ARGALA_PLANETS]
    for reference_name, reference_longitude in references.items():
        for house_number, obstructing_house in PRIMARY_ARGALA_HOUSES.items():
            entry = _build_argala_entry(
                reference_name=reference_name,
                reference_longitude=reference_longitude,
                planets=considered_planets,
                house_number=house_number,
                obstructing_house=obstructing_house,
                argala_type="Primary",
            )
            if entry is not None:
                entries.append(entry)
        for house_number, obstructing_house in SECONDARY_ARGALA_HOUSES.items():
            entry = _build_argala_entry(
                reference_name=reference_name,
                reference_longitude=reference_longitude,
                planets=considered_planets,
                house_number=house_number,
                obstructing_house=obstructing_house,
                argala_type="Secondary",
            )
            if entry is not None:
                entries.append(entry)
    return sorted(
        entries,
        key=lambda entry: (
            entry.reference,
            entry.argala_type != "Primary",
            -entry.net_strength,
            entry.house_from_reference,
        ),
    )


def _build_argala_entry(
    *,
    reference_name: str,
    reference_longitude: float,
    planets: list[PlanetPosition],
    house_number: int,
    obstructing_house: int,
    argala_type: str,
) -> ArgalaEntry | None:
    supporters = [
        planet.planet
        for planet in planets
        if _house_from_reference(reference_longitude, planet.longitude_sidereal) == house_number
    ]
    if not supporters:
        return None
    obstructors = [
        planet.planet
        for planet in planets
        if _house_from_reference(reference_longitude, planet.longitude_sidereal) == obstructing_house
    ]
    net_strength = len(supporters) - len(obstructors)
    if not obstructors:
        status = "Active"
    elif net_strength > 0:
        status = "Supported"
    elif net_strength == 0:
        status = "Contested"
    else:
        status = "Obstructed"
    return ArgalaEntry(
        reference=reference_name,
        argala_type=argala_type,
        house_from_reference=house_number,
        obstructing_house=obstructing_house,
        supporters=supporters,
        obstructors=obstructors,
        status=status,
        net_strength=net_strength,
    )


def _house_from_reference(reference_longitude: float, target_longitude: float) -> int:
    reference_sign = int(normalize_degrees(reference_longitude) // 30.0)
    target_sign = int(normalize_degrees(target_longitude) // 30.0)
    return ((target_sign - reference_sign) % 12) + 1

