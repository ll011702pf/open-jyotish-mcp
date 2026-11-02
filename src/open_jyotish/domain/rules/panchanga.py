from __future__ import annotations

from dataclasses import dataclass


TITHI_NAMES = (
    "Shukla Pratipada",
    "Shukla Dwitiya",
    "Shukla Tritiya",
    "Shukla Chaturthi",
    "Shukla Panchami",
    "Shukla Shashthi",
    "Shukla Saptami",
    "Shukla Ashtami",
    "Shukla Navami",
    "Shukla Dashami",
    "Shukla Ekadashi",
    "Shukla Dwadashi",
    "Shukla Trayodashi",
    "Shukla Chaturdashi",
    "Purnima",
    "Krishna Pratipada",
    "Krishna Dwitiya",
    "Krishna Tritiya",
    "Krishna Chaturthi",
    "Krishna Panchami",
    "Krishna Shashthi",
    "Krishna Saptami",
    "Krishna Ashtami",
    "Krishna Navami",
    "Krishna Dashami",
    "Krishna Ekadashi",
    "Krishna Dwadashi",
    "Krishna Trayodashi",
    "Krishna Chaturdashi",
    "Amavasya",
)

YOGA_NAMES = (
    "Vishkambha",
    "Priti",
    "Ayushman",
    "Saubhagya",
    "Shobhana",
    "Atiganda",
    "Sukarma",
    "Dhriti",
    "Shoola",
    "Ganda",
    "Vriddhi",
    "Dhruva",
    "Vyaghata",
    "Harshana",
    "Vajra",
    "Siddhi",
    "Vyatipata",
    "Variyana",
    "Parigha",
    "Shiva",
    "Siddha",
    "Sadhya",
    "Shubha",
    "Shukla",
    "Brahma",
    "Indra",
    "Vaidhriti",
)

KARANA_REPEAT = (
    "Bava",
    "Balava",
    "Kaulava",
    "Taitila",
    "Gara",
    "Vanija",
    "Vishti",
)

WEEKDAY_NAMES = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)


@dataclass(frozen=True, slots=True)
class PanchangaValues:
    vedic_weekday: str
    tithi_name: str
    tithi_number: int
    tithi_progress_percent: float
    yoga_name: str
    yoga_number: int
    yoga_progress_percent: float
    karana_name: str
    karana_number: int
    karana_progress_percent: float


def compute_panchanga(
    *,
    sun_longitude: float,
    moon_longitude: float,
    weekday_index: int,
) -> PanchangaValues:
    moon_sun_delta = (moon_longitude - sun_longitude) % 360.0
    tithi_number = int(moon_sun_delta // 12.0) + 1
    tithi_progress_percent = ((moon_sun_delta % 12.0) / 12.0) * 100.0

    yoga_longitude = (sun_longitude + moon_longitude) % 360.0
    yoga_span = 360.0 / 27.0
    yoga_number = int(yoga_longitude // yoga_span) + 1
    yoga_progress_percent = ((yoga_longitude % yoga_span) / yoga_span) * 100.0

    karana_index = int(moon_sun_delta // 6.0) + 1
    karana_progress_percent = ((moon_sun_delta % 6.0) / 6.0) * 100.0

    return PanchangaValues(
        vedic_weekday=WEEKDAY_NAMES[weekday_index],
        tithi_name=TITHI_NAMES[tithi_number - 1],
        tithi_number=tithi_number,
        tithi_progress_percent=tithi_progress_percent,
        yoga_name=YOGA_NAMES[yoga_number - 1],
        yoga_number=yoga_number,
        yoga_progress_percent=yoga_progress_percent,
        karana_name=resolve_karana_name(karana_index),
        karana_number=karana_index,
        karana_progress_percent=karana_progress_percent,
    )


def resolve_karana_name(karana_index: int) -> str:
    if karana_index <= 1:
        return "Kimstughna"
    if karana_index >= 58:
        return ("Shakuni", "Chatushpada", "Naga")[karana_index - 58]
    return KARANA_REPEAT[(karana_index - 2) % len(KARANA_REPEAT)]
