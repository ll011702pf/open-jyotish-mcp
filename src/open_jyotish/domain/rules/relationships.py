from __future__ import annotations

from open_jyotish.domain.models.chart_result import PlanetPosition
from open_jyotish.domain.models.chart_result import PlanetRelationshipProfile


SIGN_LORDS = {
    "Aries": "Mars",
    "Taurus": "Venus",
    "Gemini": "Mercury",
    "Cancer": "Moon",
    "Leo": "Sun",
    "Virgo": "Mercury",
    "Libra": "Venus",
    "Scorpio": "Mars",
    "Sagittarius": "Jupiter",
    "Capricorn": "Saturn",
    "Aquarius": "Saturn",
    "Pisces": "Jupiter",
}

NATURAL_RELATIONSHIPS = {
    "Sun": {
        "friend": {"Moon", "Mars", "Jupiter"},
        "enemy": {"Venus", "Saturn"},
        "neutral": {"Mercury"},
    },
    "Moon": {
        "friend": {"Sun", "Mercury"},
        "enemy": set(),
        "neutral": {"Mars", "Jupiter", "Venus", "Saturn"},
    },
    "Mars": {
        "friend": {"Sun", "Moon", "Jupiter"},
        "enemy": {"Mercury"},
        "neutral": {"Venus", "Saturn"},
    },
    "Mercury": {
        "friend": {"Sun", "Venus"},
        "enemy": {"Moon"},
        "neutral": {"Mars", "Jupiter", "Saturn"},
    },
    "Jupiter": {
        "friend": {"Sun", "Moon", "Mars"},
        "enemy": {"Mercury", "Venus"},
        "neutral": {"Saturn"},
    },
    "Venus": {
        "friend": {"Mercury", "Saturn"},
        "enemy": {"Sun", "Moon"},
        "neutral": {"Mars", "Jupiter"},
    },
    "Saturn": {
        "friend": {"Mercury", "Venus"},
        "enemy": {"Sun", "Moon", "Mars"},
        "neutral": {"Jupiter"},
    },
}

TEMPORARY_FRIEND_HOUSES = {2, 3, 4, 10, 11, 12}
TEMPORARY_ENEMY_HOUSES = {1, 5, 6, 7, 8, 9}
COMPOUND_MAP = {
    ("Friend", "Temporary Friend"): "Great Friend",
    ("Friend", "Temporary Enemy"): "Neutral",
    ("Enemy", "Temporary Friend"): "Neutral",
    ("Enemy", "Temporary Enemy"): "Great Enemy",
    ("Neutral", "Temporary Friend"): "Friend",
    ("Neutral", "Temporary Enemy"): "Enemy",
}


def build_planet_relationships(
    *,
    planets: list[PlanetPosition],
    lagna_longitude: float,
) -> list[PlanetRelationshipProfile]:
    bodies = [*planets, _build_asc_position(lagna_longitude)]
    profiles: list[PlanetRelationshipProfile] = []
    for source in bodies:
        natural: dict[str, str] = {}
        temporary: dict[str, str] = {}
        compound: dict[str, str] = {}
        for target in bodies:
            if target.planet == source.planet:
                continue
            temp_status = _temporary_status(source=source, target=target)
            temporary[target.planet] = temp_status
            natural_status = _natural_status(source.planet, target.planet)
            if natural_status is not None:
                natural[target.planet] = natural_status
                compound[target.planet] = COMPOUND_MAP[(natural_status, temp_status)]
        profiles.append(
            PlanetRelationshipProfile(
                planet=source.planet,
                natural=natural,
                temporary=temporary,
                compound=compound,
            )
        )
    return profiles


def _build_asc_position(lagna_longitude: float) -> PlanetPosition:
    sign_index = int((lagna_longitude % 360.0) // 30.0)
    return PlanetPosition(
        planet="Asc",
        longitude_sidereal=lagna_longitude,
        sign=tuple(SIGN_LORDS.keys())[sign_index],
        degree_in_sign=lagna_longitude % 30.0,
        nakshatra="-",
        nakshatra_lord="-",
        pada=1,
        house=1,
        retrograde=False,
        dignity="Neutral",
        speed_value=None,
    )


def _natural_status(source_planet: str, target_planet: str) -> str | None:
    source_map = NATURAL_RELATIONSHIPS.get(source_planet)
    if source_map is None:
        return None
    if target_planet in source_map["friend"]:
        return "Friend"
    if target_planet in source_map["enemy"]:
        return "Enemy"
    if target_planet in source_map["neutral"]:
        return "Neutral"
    return None


def _temporary_status(*, source: PlanetPosition, target: PlanetPosition) -> str:
    source_sign = int(source.longitude_sidereal % 360.0 // 30.0)
    target_sign = int(target.longitude_sidereal % 360.0 // 30.0)
    house_distance = ((target_sign - source_sign) % 12) + 1
    if house_distance in TEMPORARY_FRIEND_HOUSES:
        return "Temporary Friend"
    return "Temporary Enemy"
