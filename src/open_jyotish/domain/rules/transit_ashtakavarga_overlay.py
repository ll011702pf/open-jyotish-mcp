from __future__ import annotations

from open_jyotish.domain.models.chart_result import AshtakavargaDetails
from open_jyotish.domain.models.chart_result import TransitAshtakavargaEntry
from open_jyotish.domain.models.chart_result import TransitAshtakavargaOverlay
from open_jyotish.domain.models.chart_result import TransitSnapshot


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

PLANET_TO_BAV_LABEL = {
    "Sun": "Su",
    "Moon": "Mo",
    "Mars": "Ma",
    "Mercury": "Me",
    "Jupiter": "Ju",
    "Venus": "Ve",
    "Saturn": "Sa",
}

OVERLAY_PLANET_ORDER = {
    "Saturn": 0,
    "Jupiter": 1,
    "Rahu": 2,
    "Ketu": 3,
    "Mars": 4,
    "Sun": 5,
    "Venus": 6,
    "Mercury": 7,
    "Moon": 8,
    "Uranus": 9,
    "Neptune": 10,
    "Pluto": 11,
}


def build_transit_ashtakavarga_overlay(
    *,
    transit_snapshot: TransitSnapshot | None,
    ashtakavarga: AshtakavargaDetails | None,
) -> TransitAshtakavargaOverlay | None:
    if transit_snapshot is None or ashtakavarga is None:
        return None
    if not transit_snapshot.entries or not ashtakavarga.samudaya:
        return None

    sav_values = ashtakavarga.samudaya
    sav_average = sum(sav_values) / len(sav_values)
    peak_index = max(range(len(sav_values)), key=sav_values.__getitem__)
    peak_value = sav_values[peak_index]
    peak_sign = SIGN_SEQUENCE[peak_index]

    bav_by_label = {row.label: row.sign_values for row in ashtakavarga.binna_rows}
    entries: list[TransitAshtakavargaEntry] = []
    for transit_entry in transit_snapshot.entries:
        sign_index = _sign_index(transit_entry.transit_sign)
        if sign_index is None:
            continue
        sav_value = sav_values[sign_index]
        sav_band = _sav_band(sav_value=sav_value, sav_average=sav_average, sav_peak=peak_value)
        bav_label = PLANET_TO_BAV_LABEL.get(transit_entry.planet)
        bav_value = bav_by_label.get(bav_label, [None] * 12)[sign_index] if bav_label is not None else None
        overlay_score = sav_value + (bav_value or 0)
        entries.append(
            TransitAshtakavargaEntry(
                planet=transit_entry.planet,
                transit_sign=transit_entry.transit_sign,
                house_from_lagna=transit_entry.house_from_lagna,
                sav_value=sav_value,
                sav_band=sav_band,
                planet_bav_value=bav_value,
                overlay_score=overlay_score,
                overlay_note=_overlay_note(
                    house_from_lagna=transit_entry.house_from_lagna,
                    sav_band=sav_band,
                    relation_to_natal=transit_entry.relation_to_natal,
                ),
            )
        )

    entries.sort(key=lambda entry: (OVERLAY_PLANET_ORDER.get(entry.planet, 99), -entry.overlay_score, entry.planet))
    return TransitAshtakavargaOverlay(
        as_of_utc=transit_snapshot.as_of_utc,
        sav_average=round(sav_average, 2),
        sav_peak_sign=peak_sign,
        sav_peak_value=peak_value,
        entries=entries,
    )


def _sign_index(sign_name: str) -> int | None:
    try:
        return SIGN_SEQUENCE.index(sign_name)
    except ValueError:
        return None


def _sav_band(*, sav_value: int, sav_average: float, sav_peak: int) -> str:
    if sav_value >= max(sav_peak - 2, int(round(sav_average + 3))):
        return "Peak"
    if sav_value >= sav_average + 2:
        return "Strong"
    if sav_value >= sav_average - 2:
        return "Neutral"
    return "Sensitive"


def _overlay_note(*, house_from_lagna: int, sav_band: str, relation_to_natal: str) -> str:
    upachaya = house_from_lagna in {3, 6, 10, 11}
    dusthana = house_from_lagna in {6, 8, 12}
    if upachaya and sav_band in {"Peak", "Strong"}:
        return "Upachaya support"
    if dusthana and sav_band == "Sensitive":
        return "Watch pressure cycles"
    if relation_to_natal in {"Conjunction", "Square", "Opposition"}:
        return "Event-sensitive window"
    if relation_to_natal in {"Trine", "Sextile"} and sav_band in {"Peak", "Strong"}:
        return "Constructive timing"
    return "Monitor normally"

