from __future__ import annotations

from open_jyotish.domain.models.chart_result import DetectedDosha
from open_jyotish.domain.models.chart_result import PlanetPosition


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

MALEFICS = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}
CLASSICAL_PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")


def detect_doshas(*, planets: list[PlanetPosition], lagna_longitude: float) -> list[DetectedDosha]:
    chart_map = {planet.planet: planet for planet in planets}
    lagna_house = 1
    doshas: list[DetectedDosha] = []

    kuja_contexts = _detect_kuja(chart_map=chart_map, lagna_house=lagna_house)
    if kuja_contexts:
        doshas.append(
            DetectedDosha(
                key="kuja",
                name="Kuja Dosha",
                severity="high",
                description="Mars influences sensitive marriage/conflict houses from "
                + " and ".join(kuja_contexts)
                + ", increasing heat, impatience, and relational friction unless otherwise balanced.",
            )
        )

    if _detect_kala_sarpa(chart_map=chart_map):
        doshas.append(
            DetectedDosha(
                key="kala_sarpa",
                name="Kala Sarpa Dosha",
                severity="high",
                description="All classical planets fall within one nodal half, concentrating karmic pressure, obsession, and uneven release patterns.",
            )
        )

    grahana_contexts = _detect_grahana(chart_map=chart_map)
    if grahana_contexts:
        doshas.append(
            DetectedDosha(
                key="grahana",
                name="Grahana Dosha",
                severity="high",
                description="Luminary-node conjunctions are present: "
                + ", ".join(grahana_contexts)
                + ", intensifying eclipse-like themes around clarity, mind, or vitality.",
            )
        )

    if _detect_kemadruma(chart_map=chart_map):
        doshas.append(
            DetectedDosha(
                key="kemadruma",
                name="Kemadruma Dosha",
                severity="medium",
                description="The Moon lacks classical support by conjunction and adjacent signs, indicating emotional austerity and inconsistent support structures.",
            )
        )

    if _detect_papa_kartari(chart_map=chart_map, lagna_longitude=lagna_longitude):
        doshas.append(
            DetectedDosha(
                key="papa_kartari",
                name="Papa Kartari Dosha",
                severity="high",
                description="Malefics hem the lagna from both sides, tightening circumstances around self-expression, confidence, and freedom of action.",
            )
        )

    if _detect_shakata(chart_map=chart_map):
        doshas.append(
            DetectedDosha(
                key="shakata",
                name="Shakata Dosha",
                severity="medium",
                description="Moon and Jupiter are strained by a 6/8/12 relationship, often showing cyclical ups and downs in support, prosperity, or emotional steadiness.",
            )
        )

    return _dedupe_and_sort(doshas)


def _detect_kuja(*, chart_map: dict[str, PlanetPosition], lagna_house: int) -> list[str]:
    mars = chart_map.get("Mars")
    if mars is None or mars.house is None:
        return []
    contexts: list[str] = []
    if mars.house in {1, 2, 4, 7, 8, 12}:
        contexts.append("Lagna")
    moon = chart_map.get("Moon")
    if moon is not None and moon.house is not None:
        relative = ((mars.house - moon.house) % 12) + 1
        if relative in {1, 2, 4, 7, 8, 12}:
            contexts.append("Moon")
    return contexts


def _detect_kala_sarpa(*, chart_map: dict[str, PlanetPosition]) -> bool:
    rahu = chart_map.get("Rahu")
    ketu = chart_map.get("Ketu")
    if rahu is None or ketu is None:
        return False
    longitudes = [chart_map[name].longitude_sidereal for name in CLASSICAL_PLANETS if name in chart_map]
    if len(longitudes) != len(CLASSICAL_PLANETS):
        return False
    return _all_between_arc(longitudes=longitudes, start=rahu.longitude_sidereal, end=ketu.longitude_sidereal) or _all_between_arc(
        longitudes=longitudes,
        start=ketu.longitude_sidereal,
        end=rahu.longitude_sidereal,
    )


def _detect_grahana(*, chart_map: dict[str, PlanetPosition]) -> list[str]:
    contexts: list[str] = []
    for luminary in ("Sun", "Moon"):
        source = chart_map.get(luminary)
        if source is None:
            continue
        for node_name in ("Rahu", "Ketu"):
            node = chart_map.get(node_name)
            if node is None:
                continue
            if _angular_distance(source.longitude_sidereal, node.longitude_sidereal) <= 12.0:
                contexts.append(f"{luminary}-{node_name}")
    return contexts


def _detect_kemadruma(*, chart_map: dict[str, PlanetPosition]) -> bool:
    moon = chart_map.get("Moon")
    if moon is None:
        return False
    supported = {"Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
    if any(chart_map[name].sign == moon.sign for name in supported if name in chart_map):
        return False
    if _has_planet_in_relative_sign(chart_map=chart_map, anchor="Moon", relative=2, allowed=supported):
        return False
    if _has_planet_in_relative_sign(chart_map=chart_map, anchor="Moon", relative=12, allowed=supported):
        return False
    return True


def _detect_papa_kartari(*, chart_map: dict[str, PlanetPosition], lagna_longitude: float) -> bool:
    lagna_sign_index = int((lagna_longitude % 360.0) // 30.0)
    prev_sign = SIGN_SEQUENCE[(lagna_sign_index - 1) % 12]
    next_sign = SIGN_SEQUENCE[(lagna_sign_index + 1) % 12]
    return _sign_occupied_by_any(chart_map=chart_map, sign_name=prev_sign, planet_names=MALEFICS) and _sign_occupied_by_any(
        chart_map=chart_map,
        sign_name=next_sign,
        planet_names=MALEFICS,
    )


def _detect_shakata(*, chart_map: dict[str, PlanetPosition]) -> bool:
    moon = chart_map.get("Moon")
    jupiter = chart_map.get("Jupiter")
    if moon is None or jupiter is None or moon.house is None or jupiter.house is None:
        return False
    return ((jupiter.house - moon.house) % 12) in {5, 7, 11}


def _has_planet_in_relative_sign(
    *,
    chart_map: dict[str, PlanetPosition],
    anchor: str,
    relative: int,
    allowed: set[str],
) -> bool:
    anchor_planet = chart_map.get(anchor)
    if anchor_planet is None:
        return False
    anchor_sign = SIGN_SEQUENCE.index(anchor_planet.sign)
    target_sign = SIGN_SEQUENCE[(anchor_sign + relative - 1) % 12]
    return any(chart_map[planet].sign == target_sign for planet in allowed if planet in chart_map)


def _sign_occupied_by_any(*, chart_map: dict[str, PlanetPosition], sign_name: str, planet_names: set[str]) -> bool:
    return any(chart_map[name].sign == sign_name for name in planet_names if name in chart_map)


def _all_between_arc(*, longitudes: list[float], start: float, end: float) -> bool:
    arc = (end - start) % 360.0
    return all(((longitude - start) % 360.0) <= arc for longitude in longitudes)


def _angular_distance(left: float, right: float) -> float:
    distance = abs((left - right) % 360.0)
    return min(distance, 360.0 - distance)


def _dedupe_and_sort(doshas: list[DetectedDosha]) -> list[DetectedDosha]:
    seen: set[str] = set()
    deduped: list[DetectedDosha] = []
    severity_order = {"high": 0, "medium": 1, "low": 2}
    for dosha in doshas:
        if dosha.key in seen:
            continue
        seen.add(dosha.key)
        deduped.append(dosha)
    return sorted(deduped, key=lambda item: (severity_order.get(item.severity, 99), item.name))
