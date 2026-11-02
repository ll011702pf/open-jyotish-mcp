from __future__ import annotations

from datetime import datetime

from open_jyotish.domain.models.birth_data import BirthData
from open_jyotish.domain.models.chart_result import PlanetPosition
from open_jyotish.domain.models.chart_result import PlanetStrengthProfile
from open_jyotish.domain.models.chart_result import VargaChart


DEEP_DEBILITATION_LONGITUDES = {
    "Sun": 190.0,
    "Moon": 213.0,
    "Mars": 118.0,
    "Mercury": 345.0,
    "Jupiter": 275.0,
    "Venus": 177.0,
    "Saturn": 20.0,
}

DIG_BALA_POWERLESS_HOUSE_INDEX = {
    "Sun": 3,
    "Moon": 9,
    "Mars": 3,
    "Mercury": 6,
    "Jupiter": 6,
    "Venus": 9,
    "Saturn": 0,
}

NAISARGIKA_BALA = {
    "Sun": 60.0,
    "Moon": 51.43,
    "Mars": 17.14,
    "Mercury": 25.71,
    "Jupiter": 34.29,
    "Venus": 42.86,
    "Saturn": 8.57,
}

MAX_MOTION_SPEED = {
    "Sun": 1.05,
    "Moon": 15.5,
    "Mars": 0.8,
    "Mercury": 2.2,
    "Jupiter": 0.25,
    "Venus": 1.3,
    "Saturn": 0.14,
}

CORE_STRENGTH_PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")

SAPTAVARGA_SET = ("D1", "D2", "D3", "D7", "D9", "D12", "D30")

MALE_PLANETS = {"Sun", "Mars", "Jupiter"}
FEMALE_PLANETS = {"Moon", "Venus"}
NEUTRAL_PLANETS = {"Mercury", "Saturn"}

DAY_STRONG_PLANETS = {"Sun", "Jupiter", "Venus"}
NIGHT_STRONG_PLANETS = {"Moon", "Mars", "Saturn"}
HOUR_LORD_SEQUENCE = ("Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon")
WEEKDAY_LORDS = {
    0: "Moon",
    1: "Mars",
    2: "Mercury",
    3: "Jupiter",
    4: "Venus",
    5: "Saturn",
    6: "Sun",
}

BENEFIC_PLANETS = {"Jupiter", "Venus", "Mercury", "Moon"}
MALEFIC_PLANETS = {"Sun", "Mars", "Saturn"}

RELATIONSHIP_SCORE_MAP = {
    "Exalted": 20.0,
    "Own Sign": 15.0,
    "Neutral": 7.5,
    "Debilitated": 2.0,
    "Nodal": 7.5,
}


def compute_core_strengths(
    *,
    planets: list[PlanetPosition],
    houses: list[float],
    varga_charts: dict[str, VargaChart] | None = None,
    birth_data: BirthData | None = None,
    birth_local: datetime | None = None,
    sunrise_at: datetime | None = None,
    sunset_at: datetime | None = None,
) -> list[PlanetStrengthProfile]:
    house_midpoints = [normalize_degrees(longitude + 15.0) for longitude in houses]
    planet_map = {planet.planet: planet for planet in planets}
    strengths: list[PlanetStrengthProfile] = []
    for planet_name in CORE_STRENGTH_PLANETS:
        planet = planet_map.get(planet_name)
        if planet is None:
            continue
        uchcha_bala = compute_uchcha_bala(planet.longitude_sidereal, planet_name)
        saptavargaja_bala = compute_saptavargaja_bala(
            planet_name=planet_name,
            rasi_planet=planet,
            varga_charts=varga_charts or {},
        )
        ojhayugma_bala = compute_ojhayugma_bala(planet_name=planet_name, sign=planet.sign)
        kendradi_bala = compute_kendradi_bala(house=planet.house)
        drekkana_bala = compute_drekkana_bala(
            planet_name=planet_name,
            degree_in_sign=planet.degree_in_sign,
        )
        sthana_bala = round(
            uchcha_bala + saptavargaja_bala + ojhayugma_bala + kendradi_bala + drekkana_bala,
            2,
        )
        dig_bala = compute_dig_bala(planet.longitude_sidereal, house_midpoints, planet_name)
        natonnata_bala = compute_natonnata_bala(
            planet_name=planet_name,
            birth_local=birth_local,
            sunrise_at=sunrise_at,
            sunset_at=sunset_at,
        )
        paksha_bala = compute_paksha_bala(
            planet_name=planet_name,
            planets=planet_map,
        )
        hora_bala = compute_hora_bala(
            planet_name=planet_name,
            birth_data=birth_data,
            birth_local=birth_local,
        )
        kala_bala = round(natonnata_bala + paksha_bala + hora_bala, 2)
        naisargika_bala = NAISARGIKA_BALA[planet_name]
        motion_bala = compute_motion_bala(
            speed_value=planet.speed_value,
            planet_name=planet_name,
        )
        cheshta_bala = motion_bala
        drik_bala = compute_drik_bala(
            planet_name=planet_name,
            planets=planet_map,
        )
        ishta_phala = compute_ishta_phala(
            planet=planet,
            uchcha_bala=uchcha_bala,
            cheshta_bala=cheshta_bala,
            drik_bala=drik_bala,
        )
        kashta_phala = compute_kashta_phala(
            planet=planet,
            ishta_phala=ishta_phala,
            drik_bala=drik_bala,
        )
        total_bala = round(
            sthana_bala
            + dig_bala
            + kala_bala
            + naisargika_bala
            + cheshta_bala
            + drik_bala,
            2,
        )
        strengths.append(
            PlanetStrengthProfile(
                planet=planet_name,
                uchcha_bala=uchcha_bala,
                saptavargaja_bala=saptavargaja_bala,
                ojhayugma_bala=ojhayugma_bala,
                kendradi_bala=kendradi_bala,
                drekkana_bala=drekkana_bala,
                sthana_bala=sthana_bala,
                dig_bala=dig_bala,
                natonnata_bala=natonnata_bala,
                paksha_bala=paksha_bala,
                hora_bala=hora_bala,
                kala_bala=kala_bala,
                naisargika_bala=naisargika_bala,
                motion_bala=motion_bala,
                cheshta_bala=cheshta_bala,
                drik_bala=drik_bala,
                ishta_phala=ishta_phala,
                kashta_phala=kashta_phala,
                total_bala=total_bala,
                classification=classify_strength(total_bala),
            )
        )
    return strengths


def compute_uchcha_bala(longitude: float, planet_name: str) -> float:
    deep_debilitation = DEEP_DEBILITATION_LONGITUDES[planet_name]
    separation = shortest_angular_distance(longitude, deep_debilitation)
    return round((separation / 180.0) * 60.0, 2)


def compute_saptavargaja_bala(
    *,
    planet_name: str,
    rasi_planet: PlanetPosition,
    varga_charts: dict[str, VargaChart],
) -> float:
    score = dignity_points(rasi_planet.dignity)
    count = 1
    for varga_name in SAPTAVARGA_SET:
        if varga_name == "D1":
            continue
        varga = varga_charts.get(varga_name)
        if varga is None:
            continue
        varga_planet = next((item for item in varga.planets if item.planet == planet_name), None)
        if varga_planet is None:
            continue
        score += dignity_points(varga_planet.dignity)
        count += 1
    max_score = count * 20.0
    if max_score <= 0:
        return 0.0
    return round((score / max_score) * 45.0, 2)


def compute_ojhayugma_bala(*, planet_name: str, sign: str) -> float:
    odd_sign = sign in {"Aries", "Gemini", "Leo", "Libra", "Sagittarius", "Aquarius"}
    if planet_name in MALE_PLANETS:
        return 15.0 if odd_sign else 7.5
    if planet_name in FEMALE_PLANETS:
        return 15.0 if not odd_sign else 7.5
    return 15.0


def compute_kendradi_bala(*, house: int | None) -> float:
    if house in {1, 4, 7, 10}:
        return 60.0
    if house in {2, 5, 8, 11}:
        return 30.0
    if house in {3, 6, 9, 12}:
        return 15.0
    return 0.0


def compute_drekkana_bala(*, planet_name: str, degree_in_sign: float) -> float:
    section = min(int(degree_in_sign // 10.0), 2)
    if planet_name in MALE_PLANETS:
        return 15.0 if section == 0 else 7.5
    if planet_name in FEMALE_PLANETS:
        return 15.0 if section == 1 else 7.5
    return 15.0 if section == 2 else 7.5


def compute_dig_bala(longitude: float, house_midpoints: list[float], planet_name: str) -> float:
    powerless_house_longitude = house_midpoints[DIG_BALA_POWERLESS_HOUSE_INDEX[planet_name]]
    separation = shortest_angular_distance(longitude, powerless_house_longitude)
    return round(separation / 3.0, 2)


def compute_natonnata_bala(
    *,
    planet_name: str,
    birth_local: datetime | None,
    sunrise_at: datetime | None,
    sunset_at: datetime | None,
) -> float:
    if birth_local is None or sunrise_at is None or sunset_at is None:
        return 30.0
    is_day = sunrise_at <= birth_local <= sunset_at
    if planet_name in DAY_STRONG_PLANETS:
        return 60.0 if is_day else 15.0
    if planet_name in NIGHT_STRONG_PLANETS:
        return 60.0 if not is_day else 15.0
    return 30.0


def compute_paksha_bala(
    *,
    planet_name: str,
    planets: dict[str, PlanetPosition],
) -> float:
    sun = planets.get("Sun")
    moon = planets.get("Moon")
    if sun is None or moon is None:
        return 30.0
    elongation = shortest_angular_distance(sun.longitude_sidereal, moon.longitude_sidereal)
    waxing_strength = round((elongation / 180.0) * 60.0, 2)
    waning_strength = round(60.0 - waxing_strength, 2)
    if planet_name in {"Moon", "Jupiter", "Venus"}:
        return waxing_strength
    if planet_name in {"Sun", "Mars", "Saturn"}:
        return waning_strength
    return 30.0


def compute_hora_bala(
    *,
    planet_name: str,
    birth_data: BirthData | None,
    birth_local: datetime | None,
) -> float:
    if birth_data is None:
        return 15.0
    weekday_lord = WEEKDAY_LORDS.get(birth_data.birth_date.weekday())
    if birth_local is not None:
        hora_lord = compute_hora_lord(birth_local)
    else:
        hour_index = birth_data.birth_time.hour % 24
        hora_lord = HOUR_LORD_SEQUENCE[(hour_index + 1) % len(HOUR_LORD_SEQUENCE)]
    score = 0.0
    if weekday_lord == planet_name:
        score += 15.0
    if hora_lord == planet_name:
        score += 15.0
    return score or 7.5


def compute_hora_lord(birth_local: datetime) -> str:
    day_lord = WEEKDAY_LORDS[birth_local.weekday()]
    start_index = HOUR_LORD_SEQUENCE.index(day_lord)
    hora_index = birth_local.hour % 24
    return HOUR_LORD_SEQUENCE[(start_index + hora_index) % len(HOUR_LORD_SEQUENCE)]


def compute_motion_bala(*, speed_value: float | None, planet_name: str) -> float:
    if speed_value is None:
        return 0.0
    max_speed = MAX_MOTION_SPEED[planet_name]
    if max_speed <= 0:
        return 0.0
    return round(min(abs(speed_value) / max_speed, 1.0) * 60.0, 2)


def compute_ishta_phala(
    *,
    planet: PlanetPosition,
    uchcha_bala: float,
    cheshta_bala: float,
    drik_bala: float,
) -> float:
    dignity_component = dignity_points(planet.dignity) / 20.0
    exaltation_component = uchcha_bala / 60.0
    motion_component = cheshta_bala / 60.0
    drik_component = max(0.0, drik_bala) / 60.0
    blended = (0.35 * dignity_component) + (0.25 * exaltation_component) + (0.25 * motion_component) + (0.15 * drik_component)
    return round(max(0.0, min(60.0, blended * 60.0)), 2)


def compute_kashta_phala(
    *,
    planet: PlanetPosition,
    ishta_phala: float,
    drik_bala: float,
) -> float:
    baseline = 60.0 - ishta_phala
    if planet.dignity == "Debilitated":
        baseline += 8.0
    if planet.retrograde and planet.planet in MALEFIC_PLANETS:
        baseline += 4.0
    if drik_bala < 0:
        baseline += min(abs(drik_bala), 10.0)
    return round(max(0.0, min(60.0, baseline)), 2)


def compute_drik_bala(
    *,
    planet_name: str,
    planets: dict[str, PlanetPosition],
) -> float:
    target = planets.get(planet_name)
    if target is None:
        return 0.0
    score = 0.0
    for source_name, source in planets.items():
        if source_name == planet_name or source_name not in CORE_STRENGTH_PLANETS:
            continue
        aspect_strength = graha_drishti_strength(source_name, source.longitude_sidereal, target.longitude_sidereal)
        if aspect_strength <= 0:
            continue
        source_weight = drik_weight(source_name, planets)
        score += aspect_strength * source_weight
    return round(max(0.0, min(60.0, score)), 2)


def graha_drishti_strength(source_name: str, source_longitude: float, target_longitude: float) -> float:
    difference = normalize_degrees(target_longitude - source_longitude)
    aspects = [180.0]
    if source_name == "Mars":
        aspects.extend([90.0, 210.0])
    elif source_name == "Jupiter":
        aspects.extend([120.0, 240.0])
    elif source_name == "Saturn":
        aspects.extend([60.0, 270.0])
    best = 0.0
    for exact in aspects:
        distance = abs(difference - exact)
        distance = min(distance, 360.0 - distance)
        if distance <= 15.0:
            best = max(best, (15.0 - distance) / 15.0)
    return best * 20.0


def drik_weight(source_name: str, planets: dict[str, PlanetPosition]) -> float:
    if source_name == "Moon":
        sun = planets.get("Sun")
        moon = planets.get("Moon")
        if sun is None or moon is None:
            return 0.6
        return 0.8 if shortest_angular_distance(sun.longitude_sidereal, moon.longitude_sidereal) >= 90.0 else 0.3
    if source_name in BENEFIC_PLANETS:
        return 0.8
    if source_name in MALEFIC_PLANETS:
        return -0.8
    return 0.0


def dignity_points(dignity: str) -> float:
    return RELATIONSHIP_SCORE_MAP.get(dignity, 7.5)


def classify_strength(total_bala: float) -> str:
    if total_bala >= 300.0:
        return "Very Strong"
    if total_bala >= 225.0:
        return "Strong"
    if total_bala >= 150.0:
        return "Moderate"
    return "Weak"


def strongest_planet(strengths: list[PlanetStrengthProfile]) -> PlanetStrengthProfile | None:
    if not strengths:
        return None
    return max(strengths, key=lambda item: item.total_bala)


def weakest_planet(strengths: list[PlanetStrengthProfile]) -> PlanetStrengthProfile | None:
    if not strengths:
        return None
    return min(strengths, key=lambda item: item.total_bala)


def shortest_angular_distance(left: float, right: float) -> float:
    delta = abs(normalize_degrees(left) - normalize_degrees(right))
    return min(delta, 360.0 - delta)


def normalize_degrees(value: float) -> float:
    return value % 360.0
