from __future__ import annotations

from open_jyotish.domain.models.chart_result import PlanetPosition


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

SIGN_ORDER = (
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


def build_arudha_longitudes(*, lagna_longitude: float, planets: list[PlanetPosition]) -> dict[str, float]:
    planets_by_name = {planet.planet: planet for planet in planets}
    lagna_sign_index = int((lagna_longitude % 360.0) // 30.0)
    values: dict[str, float] = {}

    for house_number in range(1, 13):
        house_sign_index = (lagna_sign_index + house_number - 1) % 12
        house_name = "AL" if house_number == 1 else f"A{house_number}"
        arudha = _compute_arudha_for_house_sign(
            house_sign_index=house_sign_index,
            planets_by_name=planets_by_name,
        )
        values[house_name] = arudha
    values["UL"] = values["A12"]
    return values


def _compute_arudha_for_house_sign(*, house_sign_index: int, planets_by_name: dict[str, PlanetPosition]) -> float:
    sign_name = SIGN_ORDER[house_sign_index]
    lord_name = SIGN_LORDS[sign_name]
    lord = planets_by_name.get(lord_name)
    if lord is None:
        return house_sign_index * 30.0

    lord_sign_index = int((lord.longitude_sidereal % 360.0) // 30.0)
    distance = ((lord_sign_index - house_sign_index) % 12) + 1
    arudha_sign_index = (lord_sign_index + distance - 1) % 12

    same_sign = arudha_sign_index == house_sign_index
    opposite_sign = arudha_sign_index == ((house_sign_index + 6) % 12)
    if same_sign or opposite_sign:
        arudha_sign_index = (lord_sign_index + 9) % 12

    degree_in_sign = lord.longitude_sidereal % 30.0
    return (arudha_sign_index * 30.0) + degree_in_sign
