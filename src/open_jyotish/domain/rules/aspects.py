from __future__ import annotations

from open_jyotish.domain.models.chart_result import AspectEntry
from open_jyotish.domain.models.chart_result import PlanetPosition
from open_jyotish.domain.rules.strengths import normalize_degrees


SIGN_SEQUENCE = (
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
)

MOVABLE_SIGNS = {0, 3, 6, 9}
FIXED_SIGNS = {1, 4, 7, 10}
DUAL_SIGNS = {2, 5, 8, 11}
CLASSICAL_ASPECT_SOURCES = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"}

ASPECT_PATTERNS = {
    "Sun": ((180.0, "7th"),),
    "Moon": ((180.0, "7th"),),
    "Mercury": ((180.0, "7th"),),
    "Venus": ((180.0, "7th"),),
    "Mars": ((90.0, "4th"), (180.0, "7th"), (210.0, "8th")),
    "Jupiter": ((120.0, "5th"), (180.0, "7th"), (240.0, "9th")),
    "Saturn": ((60.0, "3rd"), (180.0, "7th"), (270.0, "10th")),
    "Rahu": ((180.0, "7th"),),
    "Ketu": ((180.0, "7th"),),
}


def build_aspects(
    *,
    planets: list[PlanetPosition],
    lagna_longitude: float,
) -> list[AspectEntry]:
    aspect_entries: list[AspectEntry] = []
    targets = [planet for planet in planets if planet.planet in CLASSICAL_ASPECT_SOURCES]
    targets.append(_pseudo_point("Lagna", lagna_longitude))

    graha_sources = [planet for planet in planets if planet.planet in CLASSICAL_ASPECT_SOURCES]
    for source in graha_sources:
        for target in targets:
            if target.planet == source.planet:
                continue
            aspect = _graha_aspect(source, target)
            if aspect is not None:
                aspect_entries.append(aspect)

    rasi_sources = [planet for planet in planets if planet.planet in CLASSICAL_ASPECT_SOURCES]
    for source in rasi_sources:
        source_index = _sign_index(source.longitude_sidereal)
        for target in targets:
            if target.planet == source.planet:
                continue
            target_index = _sign_index(target.longitude_sidereal)
            if target_index not in _aspected_sign_indices(source_index):
                continue
            aspect_entries.append(
                AspectEntry(
                    source=source.planet,
                    target=target.planet,
                    system="Rasi Drishti",
                    aspect_name="Sign Aspect",
                    source_sign=source.sign,
                    target_sign=target.sign,
                    house_distance=_house_distance(source.longitude_sidereal, target.longitude_sidereal),
                    orb_degrees=0.0,
                    strength=15.0,
                    classification="Full Sign",
                )
            )

    return sorted(
        aspect_entries,
        key=lambda entry: (
            entry.system != "Graha Drishti",
            -entry.strength,
            entry.source,
            entry.target,
        ),
    )


def _graha_aspect(source: PlanetPosition, target: PlanetPosition) -> AspectEntry | None:
    difference = normalize_degrees(target.longitude_sidereal - source.longitude_sidereal)
    best: tuple[float, str, float] | None = None
    for exact_angle, aspect_name in ASPECT_PATTERNS.get(source.planet, ()):
        distance = abs(difference - exact_angle)
        distance = min(distance, 360.0 - distance)
        if distance > 15.0:
            continue
        strength = round(((15.0 - distance) / 15.0) * 20.0, 2)
        if best is None or strength > best[0]:
            best = (strength, aspect_name, round(distance, 2))
    if best is None:
        return None
    strength, aspect_name, orb = best
    return AspectEntry(
        source=source.planet,
        target=target.planet,
        system="Graha Drishti",
        aspect_name=aspect_name,
        source_sign=source.sign,
        target_sign=target.sign,
        house_distance=_house_distance(source.longitude_sidereal, target.longitude_sidereal),
        orb_degrees=orb,
        strength=strength,
        classification=_classify_aspect_strength(strength),
    )


def _pseudo_point(name: str, longitude: float) -> PlanetPosition:
    sign_index = _sign_index(longitude)
    degree_in_sign = longitude % 30.0
    return PlanetPosition(
        planet=name,
        longitude_sidereal=normalize_degrees(longitude),
        sign=SIGN_SEQUENCE[sign_index],
        degree_in_sign=degree_in_sign,
        nakshatra="-",
        nakshatra_lord="",
        pada=0,
        house=1,
        dignity="Neutral",
    )


def _aspected_sign_indices(source_index: int) -> set[int]:
    if source_index in MOVABLE_SIGNS:
        excluded = (source_index + 1) % 12
        return {index for index in FIXED_SIGNS if index != excluded}
    if source_index in FIXED_SIGNS:
        excluded = (source_index - 1) % 12
        return {index for index in MOVABLE_SIGNS if index != excluded}
    return {index for index in DUAL_SIGNS if index != source_index}


def _classify_aspect_strength(strength: float) -> str:
    if strength >= 16.0:
        return "Exact"
    if strength >= 12.0:
        return "Strong"
    if strength >= 8.0:
        return "Moderate"
    return "Light"


def _sign_index(longitude: float) -> int:
    return int(normalize_degrees(longitude) // 30.0)


def _house_distance(source_longitude: float, target_longitude: float) -> int:
    source_sign = _sign_index(source_longitude)
    target_sign = _sign_index(target_longitude)
    return ((target_sign - source_sign) % 12) + 1
