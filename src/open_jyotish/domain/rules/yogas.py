from __future__ import annotations

from open_jyotish.domain.models.chart_result import DetectedYoga
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

BENEFICS = {"Mercury", "Jupiter", "Venus"}
CLASSICAL_PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
KENDRA_HOUSES = {1, 4, 7, 10}
TRIKONA_HOUSES = {1, 5, 9}
UPACHAYA_HOUSES = {3, 6, 10, 11}

OWN_SIGNS = {
    "Sun": {"Leo"},
    "Moon": {"Cancer"},
    "Mars": {"Aries", "Scorpio"},
    "Mercury": {"Gemini", "Virgo"},
    "Jupiter": {"Sagittarius", "Pisces"},
    "Venus": {"Taurus", "Libra"},
    "Saturn": {"Capricorn", "Aquarius"},
}

EXALTATION_SIGNS = {
    "Sun": "Aries",
    "Moon": "Taurus",
    "Mars": "Capricorn",
    "Mercury": "Virgo",
    "Jupiter": "Cancer",
    "Venus": "Pisces",
    "Saturn": "Libra",
}

DEBILITATION_SIGNS = {
    "Sun": "Libra",
    "Moon": "Scorpio",
    "Mars": "Cancer",
    "Mercury": "Pisces",
    "Jupiter": "Capricorn",
    "Venus": "Virgo",
    "Saturn": "Aries",
}

EXALTATION_LORDS_BY_SIGN = {sign: planet for planet, sign in EXALTATION_SIGNS.items()}


def detect_yogas(*, planets: list[PlanetPosition], lagna_longitude: float) -> list[DetectedYoga]:
    chart_map = {planet.planet: planet for planet in planets}
    lagna_sign_index = int((lagna_longitude % 360.0) // 30.0)
    yogas: list[DetectedYoga] = []
    has_sarala = _detect_sarala(chart_map=chart_map, lagna_sign_index=lagna_sign_index)
    has_harsha = _detect_harsha(chart_map=chart_map, lagna_sign_index=lagna_sign_index)
    has_vimala = _detect_vimala(chart_map=chart_map, lagna_sign_index=lagna_sign_index)

    if _same_sign(chart_map, "Sun", "Mercury"):
        yogas.append(
            DetectedYoga(
                key="budha_aditya",
                name="Budha-Aditya Yoga",
                category="solar",
                description="Sun and Mercury combine in one sign, strengthening intellect, expression, and visibility.",
            )
        )

    if _has_planet_in_relative_sign(
        chart_map=chart_map,
        anchor="Moon",
        relative=12,
        allowed={"Mars", "Mercury", "Jupiter", "Venus", "Saturn"},
    ):
        yogas.append(
            DetectedYoga(
                key="anapha",
                name="Anapha Yoga",
                category="lunar",
                description="A non-solar planet occupies the twelfth sign from the Moon, supporting self-possession and independence.",
            )
        )

    if _has_planet_in_relative_sign(
        chart_map=chart_map,
        anchor="Moon",
        relative=2,
        allowed={"Mars", "Mercury", "Jupiter", "Venus", "Saturn"},
    ):
        yogas.append(
            DetectedYoga(
                key="sunapha",
                name="Sunapha Yoga",
                category="lunar",
                description="A non-solar planet occupies the second sign from the Moon, supporting initiative, resourcefulness, and self-made momentum.",
            )
        )

    if _detect_durudhara(chart_map=chart_map):
        yogas.append(
            DetectedYoga(
                key="durudhara",
                name="Durudhara Yoga",
                category="lunar",
                description="Planets flank the Moon on both sides, increasing support, adaptability, and capacity to sustain pressure.",
            )
        )

    if _has_planet_in_relative_sign(
        chart_map=chart_map,
        anchor="Sun",
        relative=2,
        allowed={"Mars", "Mercury", "Jupiter", "Venus", "Saturn"},
    ):
        yogas.append(
            DetectedYoga(
                key="veshi",
                name="Veshi Yoga",
                category="solar",
                description="A classical planet occupies the second sign from the Sun, emphasizing initiative and result orientation.",
            )
        )

    if _has_planet_in_relative_sign(
        chart_map=chart_map,
        anchor="Sun",
        relative=12,
        allowed={"Mars", "Mercury", "Jupiter", "Venus", "Saturn"},
    ):
        yogas.append(
            DetectedYoga(
                key="vasi",
                name="Vasi Yoga",
                category="solar",
                description="A classical planet occupies the twelfth sign from the Sun, adding strategy, restraint, and behind-the-scenes influence.",
            )
        )

    if has_sarala:
        yogas.append(
            DetectedYoga(
                key="sarala_classic",
                name="Sarala Yoga",
                category="viparita",
                description="The eighth lord falls in a dusthana, indicating reversal capacity and recovery through difficult phases.",
            )
        )

    if has_harsha:
        yogas.append(
            DetectedYoga(
                key="harsha",
                name="Harsha Yoga",
                category="viparita",
                description="The sixth lord falls in a dusthana, strengthening resistance, problem-solving ability, and recovery in competition or adversity.",
            )
        )

    if has_vimala:
        yogas.append(
            DetectedYoga(
                key="vimala",
                name="Vimala Yoga",
                category="viparita",
                description="The twelfth lord falls in a dusthana, supporting detachment, expense control, and cleaner outcomes after loss-prone phases.",
            )
        )

    if has_sarala or has_harsha or has_vimala:
        yogas.append(
            DetectedYoga(
                key="viparita_raja",
                name="Viparita Raja Yoga",
                category="viparita",
                description="One or more dusthana lords produce reversal through adversity, turning difficult terrain into strategic advantage over time.",
            )
        )

    yogakarakas = _detect_yogakarakas(lagna_sign_index)
    for planet_name in yogakarakas:
        yogas.append(
            DetectedYoga(
                key=f"yogakaraka_{planet_name.lower()}",
                name="Yogakaraka",
                category="raja",
                description=f"{planet_name} simultaneously rules a kendra and a trikona for the current lagna.",
            )
        )

    yogas.extend(_detect_mahapurusha_yogas(chart_map=chart_map))

    if _detect_gaja_kesari(chart_map=chart_map):
        yogas.append(
            DetectedYoga(
                key="gaja_kesari",
                name="Gaja-Kesari Yoga",
                category="lunar",
                description="Moon and Jupiter form a kendra relationship, supporting judgment, social regard, and resilience under visibility.",
            )
        )

    if _detect_adhi(chart_map=chart_map):
        yogas.append(
            DetectedYoga(
                key="adhi",
                name="Adhi Yoga",
                category="lunar",
                description="Benefics occupy the sixth, seventh, or eighth from the Moon, supporting poise, counsel, and situational advantage under pressure.",
            )
        )

    if _detect_chandra_mangala(chart_map=chart_map):
        yogas.append(
            DetectedYoga(
                key="chandra_mangala",
                name="Chandra-Mangala Yoga",
                category="dhana",
                description="Moon and Mars combine by conjunction or kendra relationship, increasing initiative, commercial drive, and material push.",
            )
        )
 
    if _detect_dharma_karmadhipati(chart_map=chart_map, lagna_sign_index=lagna_sign_index):
        yogas.append(
            DetectedYoga(
                key="dharma_karmadhipati",
                name="Dharma-Karmadhipati Yoga",
                category="raja",
                description="The ninth and tenth lords connect by conjunction or exchange, strengthening purpose, career alignment, and executive outcomes.",
            )
        )

    if _detect_parivartana(chart_map=chart_map):
        yogas.append(
            DetectedYoga(
                key="parivartana",
                name="Parivartana Yoga",
                category="raja",
                description="Two sign lords exchange signs, creating a strong mutual reinforcement channel between their domains.",
            )
        )

    if _detect_raja_yoga_generic(chart_map=chart_map, lagna_sign_index=lagna_sign_index):
        yogas.append(
            DetectedYoga(
                key="raja_yoga_generic",
                name="Raja Yoga (Generic)",
                category="raja",
                description="A kendra lord and trikona lord form a practical sambandha by conjunction or mutual exchange.",
            )
        )

    if _detect_dhana_yoga_generic(chart_map=chart_map, lagna_sign_index=lagna_sign_index):
        yogas.append(
            DetectedYoga(
                key="dhana_yoga_generic",
                name="Dhana Yoga (Generic)",
                category="dhana",
                description="The resource houses connect through conjunction or house exchange, favoring accumulation and monetization.",
            )
        )

    if _detect_kedara(chart_map=chart_map):
        yogas.append(
            DetectedYoga(
                key="kedara",
                name="Kedara Yoga",
                category="naabhasa",
                description="The seven classical planets occupy four signs, suggesting a practical, cultivation-oriented temperament.",
            )
        )

    if _detect_chatussagara(chart_map=chart_map):
        yogas.append(
            DetectedYoga(
                key="chatussagara",
                name="Chatussagara Yoga",
                category="naabhasa",
                description="All four kendras are occupied, broadening visibility, reach, and engagement with the outer world.",
            )
        )

    if _detect_ubhayachari(chart_map=chart_map):
        yogas.append(
            DetectedYoga(
                key="ubhayachari",
                name="Ubhayachari Yoga",
                category="solar",
                description="Classical planets flank the Sun on both sides, supporting initiative, public activity, and sustained engagement with visible responsibilities.",
            )
        )

    if _detect_amala(chart_map=chart_map):
        yogas.append(
            DetectedYoga(
                key="amala",
                name="Amala Yoga",
                category="raja",
                description="A benefic occupies the tenth from the lagna or Moon, supporting cleaner reputation, contribution, and visible outcomes.",
            )
        )

    if _detect_vasumathi(chart_map=chart_map):
        yogas.append(
            DetectedYoga(
                key="vasumathi",
                name="Vasumathi Yoga",
                category="dhana",
                description="Benefics occupy upachaya houses from the lagna or Moon, favoring resource growth, support networks, and earned prosperity.",
            )
        )

    if _detect_lakshmi(chart_map=chart_map, lagna_sign_index=lagna_sign_index):
        yogas.append(
            DetectedYoga(
                key="lakshmi",
                name="Lakshmi Yoga",
                category="dhana",
                description="A strong ninth lord combines with a capable lagna lord, strengthening fortune, merit, and sustainable prosperity.",
            )
        )

    if _detect_neecha_bhanga(chart_map=chart_map):
        yogas.append(
            DetectedYoga(
                key="neecha_bhanga",
                name="Neecha-Bhanga Raja Yoga",
                category="raja",
                description="A debilitated planet receives cancellation support through dispositors or exaltation lords, improving reversal and recovery potential.",
            )
        )

    if _detect_kemadruma(chart_map=chart_map):
        yogas.append(
            DetectedYoga(
                key="kemadruma",
                name="Kemadruma Yoga",
                category="dosha",
                description="The Moon stands isolated without classical support on either side, indicating emotional austerity, self-reliance, and intermittent support gaps.",
            )
        )

    if _detect_shubha_kartari(chart_map=chart_map, lagna_sign_index=lagna_sign_index):
        yogas.append(
            DetectedYoga(
                key="shubha_kartari",
                name="Shubha Kartari Yoga",
                category="raja",
                description="Benefics surround the lagna on both sides, protecting expression, coherence, and supportive circumstances around the native.",
            )
        )

    if _detect_papa_kartari(chart_map=chart_map, lagna_sign_index=lagna_sign_index):
        yogas.append(
            DetectedYoga(
                key="papa_kartari",
                name="Papa Kartari Yoga",
                category="dosha",
                description="Malefics hem the lagna from both sides, indicating pressure, constraint, and harsher outer conditions around self-expression.",
            )
        )

    if _detect_saraswati(chart_map=chart_map):
        yogas.append(
            DetectedYoga(
                key="saraswati",
                name="Saraswati Yoga",
                category="raja",
                description="Mercury, Jupiter, and Venus receive strong angular or trinal support, emphasizing learning, articulation, and cultivated intelligence.",
            )
        )

    if _detect_parijata(chart_map=chart_map, lagna_sign_index=lagna_sign_index):
        yogas.append(
            DetectedYoga(
                key="parijata",
                name="Parijata Yoga",
                category="raja",
                description="The lagna lord and its dispositor chain remain strong, supporting gradual elevation, competence, and recognized maturation over time.",
            )
        )

    return _dedupe_and_sort(yogas)


def _same_sign(chart_map: dict[str, PlanetPosition], left: str, right: str) -> bool:
    return left in chart_map and right in chart_map and chart_map[left].sign == chart_map[right].sign


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


def _detect_sarala(*, chart_map: dict[str, PlanetPosition], lagna_sign_index: int) -> bool:
    eighth_lord = SIGN_LORDS[SIGN_SEQUENCE[(lagna_sign_index + 7) % 12]]
    eighth_lord_position = chart_map.get(eighth_lord)
    if eighth_lord_position is None:
        return False
    return eighth_lord_position.house in {6, 8, 12}


def _detect_harsha(*, chart_map: dict[str, PlanetPosition], lagna_sign_index: int) -> bool:
    sixth_lord = SIGN_LORDS[SIGN_SEQUENCE[(lagna_sign_index + 5) % 12]]
    sixth_lord_position = chart_map.get(sixth_lord)
    if sixth_lord_position is None:
        return False
    return sixth_lord_position.house in {6, 8, 12}


def _detect_vimala(*, chart_map: dict[str, PlanetPosition], lagna_sign_index: int) -> bool:
    twelfth_lord = SIGN_LORDS[SIGN_SEQUENCE[(lagna_sign_index + 11) % 12]]
    twelfth_lord_position = chart_map.get(twelfth_lord)
    if twelfth_lord_position is None:
        return False
    return twelfth_lord_position.house in {6, 8, 12}


def _detect_durudhara(*, chart_map: dict[str, PlanetPosition]) -> bool:
    return _has_planet_in_relative_sign(
        chart_map=chart_map,
        anchor="Moon",
        relative=2,
        allowed={"Mars", "Mercury", "Jupiter", "Venus", "Saturn"},
    ) and _has_planet_in_relative_sign(
        chart_map=chart_map,
        anchor="Moon",
        relative=12,
        allowed={"Mars", "Mercury", "Jupiter", "Venus", "Saturn"},
    )


def _detect_ubhayachari(*, chart_map: dict[str, PlanetPosition]) -> bool:
    return _has_planet_in_relative_sign(
        chart_map=chart_map,
        anchor="Sun",
        relative=2,
        allowed={"Mars", "Mercury", "Jupiter", "Venus", "Saturn"},
    ) and _has_planet_in_relative_sign(
        chart_map=chart_map,
        anchor="Sun",
        relative=12,
        allowed={"Mars", "Mercury", "Jupiter", "Venus", "Saturn"},
    )


def _detect_yogakarakas(lagna_sign_index: int) -> list[str]:
    kendra_houses = {1, 4, 7, 10}
    trikona_houses = {1, 5, 9}
    ownership: dict[str, set[int]] = {}
    for house in range(1, 13):
        sign = SIGN_SEQUENCE[(lagna_sign_index + house - 1) % 12]
        lord = SIGN_LORDS[sign]
        ownership.setdefault(lord, set()).add(house)
    results: list[str] = []
    for planet_name, houses in ownership.items():
        if houses & kendra_houses and houses & trikona_houses and houses != {1}:
            results.append(planet_name)
    return results


def _detect_mahapurusha_yogas(*, chart_map: dict[str, PlanetPosition]) -> list[DetectedYoga]:
    definitions = (
        (
            "Mars",
            "ruchaka",
            "Ruchaka Yoga",
            "Mars occupies a kendra in own or exalted sign, emphasizing courage, action, and strategic force.",
        ),
        (
            "Mercury",
            "bhadra",
            "Bhadra Yoga",
            "Mercury occupies a kendra in own or exalted sign, supporting intellect, craft, and analytical precision.",
        ),
        (
            "Jupiter",
            "hamsa",
            "Hamsa Yoga",
            "Jupiter occupies a kendra in own or exalted sign, strengthening counsel, ethics, and wisdom.",
        ),
        (
            "Venus",
            "malavya",
            "Malavya Yoga",
            "Venus occupies a kendra in own or exalted sign, supporting refinement, comfort, attraction, and relational grace.",
        ),
        (
            "Saturn",
            "sasa",
            "Sasa Yoga",
            "Saturn occupies a kendra in own or exalted sign, emphasizing endurance, organization, and long-range execution.",
        ),
    )
    yogas: list[DetectedYoga] = []
    for planet_name, key, name, description in definitions:
        planet = chart_map.get(planet_name)
        if planet is None or planet.house not in {1, 4, 7, 10}:
            continue
        if planet.sign in OWN_SIGNS[planet_name] or planet.sign == EXALTATION_SIGNS[planet_name]:
            yogas.append(
                DetectedYoga(
                    key=key,
                    name=name,
                    category="mahapurusha",
                    description=description,
                )
            )
    return yogas


def _detect_gaja_kesari(*, chart_map: dict[str, PlanetPosition]) -> bool:
    moon = chart_map.get("Moon")
    jupiter = chart_map.get("Jupiter")
    if moon is None or jupiter is None:
        return False
    if moon.house is None or jupiter.house is None:
        return False
    return ((jupiter.house - moon.house) % 12) in {0, 3, 6, 9}


def _detect_adhi(*, chart_map: dict[str, PlanetPosition]) -> bool:
    moon = chart_map.get("Moon")
    if moon is None or moon.house is None:
        return False
    benefics = [chart_map[name] for name in ("Mercury", "Jupiter", "Venus") if name in chart_map]
    return any(
        benefic.house is not None and ((benefic.house - moon.house) % 12) in {5, 6, 7}
        for benefic in benefics
    )


def _detect_chandra_mangala(*, chart_map: dict[str, PlanetPosition]) -> bool:
    moon = chart_map.get("Moon")
    mars = chart_map.get("Mars")
    if moon is None or mars is None or moon.house is None or mars.house is None:
        return False
    return moon.sign == mars.sign or ((mars.house - moon.house) % 12) in {0, 3, 6, 9}


def _detect_dharma_karmadhipati(*, chart_map: dict[str, PlanetPosition], lagna_sign_index: int) -> bool:
    ownership = _house_lord_map(lagna_sign_index)
    ninth_lord = ownership[9]
    tenth_lord = ownership[10]
    if ninth_lord not in chart_map or tenth_lord not in chart_map:
        return False
    if chart_map[ninth_lord].sign == chart_map[tenth_lord].sign:
        return True
    return _is_exchange(chart_map=chart_map, planet_a=ninth_lord, planet_b=tenth_lord)


def _detect_parivartana(*, chart_map: dict[str, PlanetPosition]) -> bool:
    classical = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
    for left in classical:
        for right in classical:
            if left >= right:
                continue
            if _is_exchange(chart_map=chart_map, planet_a=left, planet_b=right):
                return True
    return False


def _detect_raja_yoga_generic(*, chart_map: dict[str, PlanetPosition], lagna_sign_index: int) -> bool:
    ownership = _house_lord_map(lagna_sign_index)
    kendra_lords = {ownership[house] for house in (1, 4, 7, 10)}
    trikona_lords = {ownership[house] for house in (1, 5, 9)}
    for left in kendra_lords:
        for right in trikona_lords:
            if left == right or left not in chart_map or right not in chart_map:
                continue
            if chart_map[left].sign == chart_map[right].sign:
                return True
            if _is_exchange(chart_map=chart_map, planet_a=left, planet_b=right):
                return True
    return False


def _detect_dhana_yoga_generic(*, chart_map: dict[str, PlanetPosition], lagna_sign_index: int) -> bool:
    ownership = _house_lord_map(lagna_sign_index)
    second_lord = ownership[2]
    eleventh_lord = ownership[11]
    if second_lord not in chart_map or eleventh_lord not in chart_map:
        return False
    if chart_map[second_lord].sign == chart_map[eleventh_lord].sign:
        return True
    if chart_map[second_lord].house == 11 or chart_map[eleventh_lord].house == 2:
        return True
    if chart_map[second_lord].house in {2, 5, 9, 11} and chart_map[eleventh_lord].house in {2, 5, 9, 11}:
        return True
    return _is_exchange(chart_map=chart_map, planet_a=second_lord, planet_b=eleventh_lord)


def _detect_kedara(*, chart_map: dict[str, PlanetPosition]) -> bool:
    classical = [chart_map[name].sign for name in CLASSICAL_PLANETS if name in chart_map]
    return len(classical) == 7 and len(set(classical)) == 4


def _detect_chatussagara(*, chart_map: dict[str, PlanetPosition]) -> bool:
    occupied = {planet.house for planet in chart_map.values() if planet.house is not None}
    return KENDRA_HOUSES.issubset(occupied)


def _detect_shubha_kartari(*, chart_map: dict[str, PlanetPosition], lagna_sign_index: int) -> bool:
    return _sign_occupied_by_any(
        chart_map=chart_map,
        sign_name=SIGN_SEQUENCE[(lagna_sign_index + 1) % 12],
        planet_names=BENEFICS,
    ) and _sign_occupied_by_any(
        chart_map=chart_map,
        sign_name=SIGN_SEQUENCE[(lagna_sign_index - 1) % 12],
        planet_names=BENEFICS,
    )


def _detect_papa_kartari(*, chart_map: dict[str, PlanetPosition], lagna_sign_index: int) -> bool:
    malefics = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}
    return _sign_occupied_by_any(
        chart_map=chart_map,
        sign_name=SIGN_SEQUENCE[(lagna_sign_index + 1) % 12],
        planet_names=malefics,
    ) and _sign_occupied_by_any(
        chart_map=chart_map,
        sign_name=SIGN_SEQUENCE[(lagna_sign_index - 1) % 12],
        planet_names=malefics,
    )


def _detect_amala(*, chart_map: dict[str, PlanetPosition]) -> bool:
    moon = chart_map.get("Moon")
    for planet_name in BENEFICS:
        planet = chart_map.get(planet_name)
        if planet is None or planet.house is None:
            continue
        if planet.house == 10:
            return True
        if moon is not None and moon.house is not None and ((planet.house - moon.house) % 12) == 9:
            return True
    return False


def _detect_vasumathi(*, chart_map: dict[str, PlanetPosition]) -> bool:
    moon = chart_map.get("Moon")
    lagna_hits = 0
    moon_hits = 0
    for planet_name in BENEFICS:
        planet = chart_map.get(planet_name)
        if planet is None or planet.house is None:
            continue
        if planet.house in UPACHAYA_HOUSES:
            lagna_hits += 1
        if moon is not None and moon.house is not None and ((planet.house - moon.house) % 12) in {2, 5, 9, 10}:
            moon_hits += 1
    return lagna_hits >= 2 or moon_hits >= 2


def _detect_saraswati(*, chart_map: dict[str, PlanetPosition]) -> bool:
    mercury = chart_map.get("Mercury")
    jupiter = chart_map.get("Jupiter")
    venus = chart_map.get("Venus")
    if mercury is None or jupiter is None or venus is None:
        return False
    if mercury.house not in {1, 2, 4, 5, 7, 9, 10}:
        return False
    if jupiter.house not in {1, 2, 4, 5, 7, 9, 10}:
        return False
    if venus.house not in {1, 2, 4, 5, 7, 9, 10}:
        return False
    return mercury.sign in OWN_SIGNS["Mercury"] or mercury.sign == EXALTATION_SIGNS["Mercury"]


def _detect_lakshmi(*, chart_map: dict[str, PlanetPosition], lagna_sign_index: int) -> bool:
    ownership = _house_lord_map(lagna_sign_index)
    lagna_lord = chart_map.get(ownership[1])
    ninth_lord = chart_map.get(ownership[9])
    if lagna_lord is None or ninth_lord is None or ninth_lord.house is None:
        return False
    return (
        _is_planet_strong(lagna_lord)
        and _is_planet_strong(ninth_lord)
        and ninth_lord.house in KENDRA_HOUSES | TRIKONA_HOUSES
    )


def _detect_parijata(*, chart_map: dict[str, PlanetPosition], lagna_sign_index: int) -> bool:
    lagna_lord_name = _house_lord_map(lagna_sign_index)[1]
    lagna_lord = chart_map.get(lagna_lord_name)
    if lagna_lord is None:
        return False
    dispositor_name = SIGN_LORDS[lagna_lord.sign]
    dispositor = chart_map.get(dispositor_name)
    if dispositor is None:
        return False
    return _is_planet_strong(lagna_lord) and _is_planet_strong(dispositor)


def _detect_neecha_bhanga(*, chart_map: dict[str, PlanetPosition]) -> bool:
    for planet_name in CLASSICAL_PLANETS:
        position = chart_map.get(planet_name)
        if position is None or position.sign != DEBILITATION_SIGNS.get(planet_name):
            continue
        sign_lord = SIGN_LORDS[position.sign]
        exalted_lord = EXALTATION_LORDS_BY_SIGN.get(position.sign)
        if _is_kendra_from_lagna_or_moon(chart_map=chart_map, planet_name=sign_lord):
            return True
        if exalted_lord and _is_kendra_from_lagna_or_moon(chart_map=chart_map, planet_name=exalted_lord):
            return True
        if sign_lord in chart_map and chart_map[sign_lord].sign == position.sign:
            return True
        if exalted_lord and exalted_lord in chart_map and chart_map[exalted_lord].sign == position.sign:
            return True
    return False


def _detect_kemadruma(*, chart_map: dict[str, PlanetPosition]) -> bool:
    moon = chart_map.get("Moon")
    if moon is None:
        return False
    supported = {"Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
    if any(chart_map[name].sign == moon.sign for name in supported if name in chart_map):
        return False
    if _has_planet_in_relative_sign(
        chart_map=chart_map,
        anchor="Moon",
        relative=2,
        allowed=supported,
    ):
        return False
    if _has_planet_in_relative_sign(
        chart_map=chart_map,
        anchor="Moon",
        relative=12,
        allowed=supported,
    ):
        return False
    return True


def _house_lord_map(lagna_sign_index: int) -> dict[int, str]:
    return {
        house: SIGN_LORDS[SIGN_SEQUENCE[(lagna_sign_index + house - 1) % 12]]
        for house in range(1, 13)
    }


def _is_exchange(*, chart_map: dict[str, PlanetPosition], planet_a: str, planet_b: str) -> bool:
    position_a = chart_map.get(planet_a)
    position_b = chart_map.get(planet_b)
    if position_a is None or position_b is None:
        return False
    return SIGN_LORDS[position_a.sign] == planet_b and SIGN_LORDS[position_b.sign] == planet_a


def _sign_occupied_by_any(*, chart_map: dict[str, PlanetPosition], sign_name: str, planet_names: set[str]) -> bool:
    return any(chart_map[name].sign == sign_name for name in planet_names if name in chart_map)


def _is_planet_strong(planet: PlanetPosition) -> bool:
    return (
        planet.sign in OWN_SIGNS.get(planet.planet, set())
        or planet.sign == EXALTATION_SIGNS.get(planet.planet)
        or planet.house in KENDRA_HOUSES | TRIKONA_HOUSES
    )


def _is_kendra_from_lagna_or_moon(*, chart_map: dict[str, PlanetPosition], planet_name: str) -> bool:
    planet = chart_map.get(planet_name)
    if planet is None or planet.house is None:
        return False
    if planet.house in KENDRA_HOUSES:
        return True
    moon = chart_map.get("Moon")
    if moon is None or moon.house is None:
        return False
    return ((planet.house - moon.house) % 12) in {0, 3, 6, 9}


def _dedupe_and_sort(yogas: list[DetectedYoga]) -> list[DetectedYoga]:
    seen: set[str] = set()
    deduped: list[DetectedYoga] = []
    for yoga in yogas:
        if yoga.key in seen:
            continue
        seen.add(yoga.key)
        deduped.append(yoga)
    return sorted(deduped, key=lambda item: (item.category, item.name))
