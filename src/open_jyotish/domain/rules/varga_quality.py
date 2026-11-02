from __future__ import annotations

from open_jyotish.domain.models.chart_result import PlanetPosition
from open_jyotish.domain.models.chart_result import PlanetVargaQualityProfile
from open_jyotish.domain.models.chart_result import VimsopakaEntry
from open_jyotish.domain.models.chart_result import VargaChart


RELATIONSHIP_VALUES = [
    [4, 1, 2, 2, 5, 2, 0, 3, 3, 1, 1, 3],
    [2, 4, 3, 5, 3, 3, 2, 0, 2, 2, 2, 2],
    [5, 2, 1, 0, 3, 1, 2, 5, 3, 4, 2, 3],
    [2, 3, 5, 1, 3, 5, 3, 2, 2, 2, 2, 0],
    [3, 1, 1, 4, 3, 3, 1, 3, 5, 0, 2, 5],
    [2, 5, 3, 1, 1, 0, 5, 2, 3, 3, 3, 4],
    [0, 3, 3, 1, 1, 3, 4, 1, 2, 5, 5, 2],
    [1, 4, 4, 1, 1, 3, 3, 0, 0, 3, 1, 3],
    [1, 0, 0, 1, 1, 3, 3, 4, 4, 3, 1, 3],
]

MOOLA_TRIKONA_SIGNS = {
    "Sun": 4,
    "Moon": 1,
    "Mars": 0,
    "Mercury": 5,
    "Jupiter": 8,
    "Venus": 6,
    "Saturn": 10,
    "Rahu": 5,
    "Ketu": 11,
}

RELATIONSHIP_SCORE_MAP = {5: 20.0, 4: 18.0, 3: 15.0, 2: 10.0, 1: 7.0, 0: 5.0}
PLANET_ORDER = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")
PLANET_INDEX = {name: index for index, name in enumerate(PLANET_ORDER)}

VIMSOPAKA_GROUPS = {
    "Dasa Varga (10)": {1: 3.0, 2: 1.5, 3: 1.5, 7: 1.5, 9: 1.5, 10: 1.5, 12: 1.5, 16: 1.5, 30: 1.5, 60: 5.0},
    "Shodasa Varga (16)": {1: 3.5, 2: 1.0, 3: 1.0, 4: 0.5, 7: 0.5, 9: 3.0, 10: 0.5, 12: 0.5, 16: 2.0, 20: 0.5, 24: 0.5, 27: 0.5, 30: 1.0, 40: 0.5, 45: 0.5, 60: 4.0},
    "Sapta Varga (7)": {1: 5.0, 2: 2.0, 3: 3.0, 7: 1.0, 9: 2.5, 12: 4.5, 30: 2.0},
    "Shad Varga (6)": {1: 6.0, 2: 2.0, 3: 4.0, 9: 5.0, 12: 2.0, 30: 1.0},
}

VAISESHIKAMSA_GROUPS = {
    "Dasa Varga (10)": {1, 2, 3, 7, 9, 10, 12, 16, 30, 60},
    "Shodasa Varga (16)": {1, 2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60},
}

VAISESHIKAMSA_NAMES = {
    "Dasa Varga (10)": {
        2: "Paarijaata",
        3: "Uttama",
        4: "Gopura",
        5: "Simhaasana",
        6: "Paaraavata",
        7: "Devaloka",
        8: "Brahmaloka",
        9: "Airaavata",
        10: "Sreedhaama",
    },
    "Shodasa Varga (16)": {
        2: "Bhedaka",
        3: "Kusuma",
        4: "Nagapurusha",
        5: "Kanduka",
        6: "Kerala",
        7: "Kalpavriksha",
        8: "Chandanavana",
        9: "Poornachandra",
        10: "Uchchaisrava",
        11: "Dhanvantari",
        12: "Sooryakaanta",
        13: "Vidruma",
        14: "Indraasana",
        15: "Goloka",
        16: "Sree Vallabha",
    },
}


def compute_varga_quality_profiles(
    *,
    rasi_planets: list[PlanetPosition],
    varga_charts: dict[str, VargaChart],
) -> list[PlanetVargaQualityProfile]:
    charts_by_factor = {1: VargaChart(name="D1", lagna_longitude=0.0, planets=rasi_planets)}
    for name, chart in varga_charts.items():
        factor = int(name[1:])
        charts_by_factor[factor] = chart

    profiles: list[PlanetVargaQualityProfile] = []
    for planet in PLANET_ORDER:
        vimsopaka_entries = [
            compute_vimsopaka_entry(
                planet=planet,
                charts_by_factor=charts_by_factor,
                group_label=group_label,
                weights=weights,
            )
            for group_label, weights in VIMSOPAKA_GROUPS.items()
        ]
        vaiseshikamsa_entries = [
            compute_vaiseshikamsa_entry(
                planet=planet,
                charts_by_factor=charts_by_factor,
                group_label=group_label,
                factors=factors,
            )
            for group_label, factors in VAISESHIKAMSA_GROUPS.items()
        ]
        profiles.append(
            PlanetVargaQualityProfile(
                planet=planet,
                vimsopaka=vimsopaka_entries,
                vaiseshikamsa=vaiseshikamsa_entries,
            )
        )
    return profiles


def compute_vimsopaka_entry(
    *,
    planet: str,
    charts_by_factor: dict[int, VargaChart],
    group_label: str,
    weights: dict[int, float],
) -> VimsopakaEntry:
    qualifying_vargas: list[str] = []
    weighted_score = 0.0
    total_weight = sum(weights.values())
    for factor, weight in weights.items():
        chart = charts_by_factor.get(factor)
        if chart is None:
            continue
        position = next((item for item in chart.planets if item.planet == planet), None)
        if position is None:
            continue
        sign_index = int((position.longitude_sidereal % 360.0) // 30.0)
        relation = RELATIONSHIP_VALUES[PLANET_INDEX[planet]][sign_index]
        score_value = RELATIONSHIP_SCORE_MAP[relation]
        weighted_score += weight * score_value / 20.0
        if sign_index == MOOLA_TRIKONA_SIGNS[planet] or relation > 3:
            qualifying_vargas.append(f"D{factor}")
    raw_score = round(weighted_score, 2)
    percent = round((raw_score / total_weight) * 100.0, 2) if total_weight else 0.0
    return VimsopakaEntry(
        label=group_label,
        score=raw_score,
        percent=percent,
        qualifying_count=len(qualifying_vargas),
        qualifying_vargas=qualifying_vargas,
    )


def compute_vaiseshikamsa_entry(
    *,
    planet: str,
    charts_by_factor: dict[int, VargaChart],
    group_label: str,
    factors: set[int],
) -> str:
    qualifying_vargas: list[str] = []
    for factor in sorted(factors):
        chart = charts_by_factor.get(factor)
        if chart is None:
            continue
        position = next((item for item in chart.planets if item.planet == planet), None)
        if position is None:
            continue
        sign_index = int((position.longitude_sidereal % 360.0) // 30.0)
        relation = RELATIONSHIP_VALUES[PLANET_INDEX[planet]][sign_index]
        if sign_index == MOOLA_TRIKONA_SIGNS[planet] or relation > 3:
            qualifying_vargas.append(f"D{factor}")
    count = len(qualifying_vargas)
    special_name = VAISESHIKAMSA_NAMES[group_label].get(count)
    if special_name is None:
        return f"{group_label}: -"
    return f"{group_label}: {count}-{special_name} ({', '.join(qualifying_vargas)})"
