from __future__ import annotations


PLANET_DIGNITY_SIGNS = {
    "Sun": {"exaltation": "Aries", "debilitation": "Libra", "own": {"Leo"}},
    "Moon": {"exaltation": "Taurus", "debilitation": "Scorpio", "own": {"Cancer"}},
    "Mars": {"exaltation": "Capricorn", "debilitation": "Cancer", "own": {"Aries", "Scorpio"}},
    "Mercury": {"exaltation": "Virgo", "debilitation": "Pisces", "own": {"Gemini", "Virgo"}},
    "Jupiter": {"exaltation": "Cancer", "debilitation": "Capricorn", "own": {"Sagittarius", "Pisces"}},
    "Venus": {"exaltation": "Pisces", "debilitation": "Virgo", "own": {"Taurus", "Libra"}},
    "Saturn": {"exaltation": "Libra", "debilitation": "Aries", "own": {"Capricorn", "Aquarius"}},
}


def resolve_planet_dignity(planet_name: str, sign_name: str) -> str:
    if planet_name in {"Rahu", "Ketu"}:
        return "Nodal"
    rules = PLANET_DIGNITY_SIGNS.get(planet_name)
    if rules is None:
        return "Outer"
    if sign_name == rules["exaltation"]:
        return "Exalted"
    if sign_name == rules["debilitation"]:
        return "Debilitated"
    if sign_name in rules["own"]:
        return "Own Sign"
    return "Neutral"
