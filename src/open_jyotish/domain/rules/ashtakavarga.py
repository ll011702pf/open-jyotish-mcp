from __future__ import annotations

from copy import deepcopy

from open_jyotish.domain.models.chart_result import AshtakavargaDetails
from open_jyotish.domain.models.chart_result import AshtakavargaPinda
from open_jyotish.domain.models.chart_result import AshtakavargaRow
from open_jyotish.domain.models.chart_result import PlanetPosition


ASHTAKA_VARGA_DICT = {
    "0": [[1, 2, 4, 7, 8, 9, 10, 11], [3, 6, 10, 11], [1, 2, 4, 7, 8, 9, 10, 11], [3, 5, 6, 9, 10, 11, 12], [5, 6, 9, 11], [6, 7, 12], [1, 2, 4, 7, 8, 9, 10, 11], [3, 4, 6, 10, 11, 12]],
    "1": [[3, 6, 7, 8, 10, 11], [1, 3, 6, 7, 9, 10, 11], [2, 3, 5, 6, 10, 11], [1, 3, 4, 5, 7, 8, 10, 11], [1, 2, 4, 7, 8, 10, 11], [3, 4, 5, 7, 9, 10, 11], [3, 5, 6, 11], [3, 6, 10, 11]],
    "2": [[3, 5, 6, 10, 11], [3, 6, 11], [1, 2, 4, 7, 8, 10, 11], [3, 5, 6, 11], [6, 10, 11, 12], [6, 8, 11, 12], [1, 4, 7, 8, 9, 10, 11], [1, 3, 6, 10, 11]],
    "3": [[5, 6, 9, 11, 12], [2, 4, 6, 8, 10, 11], [1, 2, 4, 7, 8, 9, 10, 11], [1, 3, 5, 6, 9, 10, 11, 12], [6, 8, 11, 12], [1, 2, 3, 4, 5, 8, 9, 11], [1, 2, 4, 7, 8, 9, 10, 11], [1, 2, 4, 6, 8, 10, 11]],
    "4": [[1, 2, 3, 4, 7, 8, 9, 10, 11], [2, 5, 7, 9, 11], [1, 2, 4, 7, 8, 10, 11], [1, 2, 4, 5, 6, 9, 10, 11], [1, 2, 3, 4, 7, 8, 10, 11], [2, 5, 6, 9, 10, 11], [3, 5, 6, 12], [1, 2, 4, 5, 6, 7, 9, 10, 11]],
    "5": [[8, 11, 12], [1, 2, 3, 4, 5, 8, 9, 11, 12], [3, 4, 6, 9, 11, 12], [3, 5, 6, 9, 11], [5, 8, 9, 10, 11], [1, 2, 3, 4, 5, 8, 9, 10, 11], [3, 4, 5, 8, 9, 10, 11], [1, 2, 3, 4, 5, 8, 9, 11]],
    "6": [[1, 2, 4, 7, 8, 10, 11], [3, 6, 11], [3, 5, 6, 10, 11, 12], [6, 8, 9, 10, 11, 12], [5, 6, 11, 12], [6, 11, 12], [3, 5, 6, 11], [1, 3, 4, 6, 10, 11]],
    "7": [[3, 4, 6, 10, 11, 12], [3, 6, 10, 11, 12], [1, 3, 6, 10, 11], [1, 2, 4, 6, 8, 10, 11], [1, 2, 4, 5, 6, 7, 9, 10, 11], [1, 2, 3, 4, 5, 8, 9], [1, 3, 4, 6, 10, 11], [3, 6, 10, 11]],
}

DISPLAY_ROW_ORDER = ("As", "Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa")
ROW_INDEX_BY_LABEL = {"Su": 0, "Mo": 1, "Ma": 2, "Me": 3, "Ju": 4, "Ve": 5, "Sa": 6, "As": 7}
PLANET_TO_AV_ID = {"Sun": 0, "Moon": 1, "Mars": 2, "Mercury": 3, "Jupiter": 4, "Venus": 5, "Saturn": 6}
AV_ID_TO_LABEL = {0: "Su", 1: "Mo", 2: "Ma", 3: "Me", 4: "Ju", 5: "Ve", 6: "Sa", 7: "As"}
ASHTAKAVARGA_RASI_OWNERS = [4, 3, (0, 7), (2, 5), (8, 11), (1, 6), (9, 10)]
ASHTAKAVARGA_RASIMANA_MULTIPLIERS = [7, 10, 8, 4, 10, 6, 7, 8, 9, 5, 11, 12]
ASHTAKAVARGA_GRAHAMANA_MULTIPLIERS = [5, 5, 8, 5, 10, 7, 5]


def compute_ashtakavarga(*, planets: list[PlanetPosition], lagna_longitude: float) -> AshtakavargaDetails:
    house_to_tokens = build_house_to_tokens(planets=planets, lagna_longitude=lagna_longitude)
    planet_to_house = build_planet_to_house(house_to_tokens)

    binna_matrix = [[0 for _ in range(12)] for _ in range(8)]
    for row_index in range(8):
        for contributor_index, target_offsets in enumerate(ASHTAKA_VARGA_DICT[str(row_index)]):
            house_index = planet_to_house["L"] if contributor_index == 7 else planet_to_house[contributor_index]
            for offset in target_offsets:
                target_house = (offset - 1 + house_index) % 12
                binna_matrix[row_index][target_house] += 1

    samudaya = [sum(binna_matrix[row_index][sign] for row_index in range(7)) for sign in range(12)]
    trikona_matrix = apply_trikona_sodhana(binna_matrix[:7])
    ekadhipatya_matrix = apply_ekadhipatya_sodhana(trikona_matrix, house_to_tokens)
    pinda_rows = build_pinda_rows(ekadhipatya_matrix, house_to_tokens)

    return AshtakavargaDetails(
        binna_rows=build_rows(binna_matrix),
        samudaya=samudaya,
        trikona_rows=build_rows(trikona_matrix, include_lagna=False),
        ekadhipatya_rows=build_rows(ekadhipatya_matrix, include_lagna=False),
        pinda_rows=pinda_rows,
    )


def build_house_to_tokens(*, planets: list[PlanetPosition], lagna_longitude: float) -> list[str]:
    tokens = [[] for _ in range(12)]
    for planet in planets:
        av_id = PLANET_TO_AV_ID.get(planet.planet)
        if av_id is None:
            continue
        sign_index = int((planet.longitude_sidereal % 360.0) // 30.0)
        tokens[sign_index].append(str(av_id))
    lagna_sign_index = int((lagna_longitude % 360.0) // 30.0)
    tokens[lagna_sign_index].append("L")
    return ["/".join(sign_tokens) for sign_tokens in tokens]


def build_planet_to_house(house_to_tokens: list[str]) -> dict[int | str, int]:
    mapping: dict[int | str, int] = {}
    for house_index, token_string in enumerate(house_to_tokens):
        if not token_string:
            continue
        for token in token_string.split("/"):
            if token == "L":
                mapping["L"] = house_index
            else:
                mapping[int(token)] = house_index
    return mapping


def build_rows(matrix: list[list[int]], *, include_lagna: bool = True) -> list[AshtakavargaRow]:
    labels = DISPLAY_ROW_ORDER if include_lagna else DISPLAY_ROW_ORDER[1:]
    return [
        AshtakavargaRow(label=label, sign_values=list(matrix[ROW_INDEX_BY_LABEL[label]]))
        for label in labels
    ]


def apply_trikona_sodhana(matrix: list[list[int]]) -> list[list[int]]:
    result = deepcopy(matrix)
    for row_index in range(7):
        for start in range(4):
            first = result[row_index][start]
            fifth = result[row_index][start + 4]
            ninth = result[row_index][start + 8]
            if first == 0 or fifth == 0 or ninth == 0:
                continue
            if first == fifth == ninth:
                result[row_index][start] = 0
                result[row_index][start + 4] = 0
                result[row_index][start + 8] = 0
                continue
            min_value = min(first, fifth, ninth)
            result[row_index][start] -= min_value
            result[row_index][start + 4] -= min_value
            result[row_index][start + 8] -= min_value
    return result


def apply_ekadhipatya_sodhana(matrix: list[list[int]], house_to_tokens: list[str]) -> list[list[int]]:
    result = deepcopy(matrix)
    for row_index in range(2, 7):
        sign_a, sign_b = ASHTAKAVARGA_RASI_OWNERS[row_index]
        occupied_a = bool(house_to_tokens[sign_a].strip())
        occupied_b = bool(house_to_tokens[sign_b].strip())
        value_a = result[row_index][sign_a]
        value_b = result[row_index][sign_b]
        if value_a == 0 or value_b == 0 or (occupied_a and occupied_b):
            continue
        if not occupied_a and not occupied_b:
            if value_a == value_b:
                result[row_index][sign_a] = 0
                result[row_index][sign_b] = 0
            else:
                min_value = min(value_a, value_b)
                result[row_index][sign_a] = min_value
                result[row_index][sign_b] = min_value
            continue
        if occupied_a:
            result[row_index][sign_b] = 0 if value_b < value_a else value_a
        else:
            result[row_index][sign_a] = 0 if value_a < value_b else value_b
    return result


def build_pinda_rows(matrix: list[list[int]], house_to_tokens: list[str]) -> list[AshtakavargaPinda]:
    planet_to_house = build_planet_to_house(house_to_tokens)
    ordered_houses = [planet_to_house[index] for index in range(7)]
    rows: list[AshtakavargaPinda] = []
    for row_index in range(7):
        rasi_pinda = sum(
            matrix[row_index][sign_index] * ASHTAKAVARGA_RASIMANA_MULTIPLIERS[sign_index]
            for sign_index in range(12)
        )
        graha_pinda = sum(
            ASHTAKAVARGA_GRAHAMANA_MULTIPLIERS[planet_index] * matrix[row_index][house_index]
            for planet_index, house_index in enumerate(ordered_houses)
        )
        rows.append(
            AshtakavargaPinda(
                label=AV_ID_TO_LABEL[row_index],
                rasi_pinda=rasi_pinda,
                graha_pinda=graha_pinda,
                sodhya_pinda=rasi_pinda + graha_pinda,
            )
        )
    return rows
