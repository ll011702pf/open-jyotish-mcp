from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from datetime import time


DAY_RULERS = (
    (0, 1, 2, 3, 4, 5, 6, -1),
    (1, 2, 3, 4, 5, 6, -1, 0),
    (2, 3, 4, 5, 6, -1, 0, 1),
    (3, 4, 5, 6, -1, 0, 1, 2),
    (4, 5, 6, -1, 0, 1, 2, 3),
    (5, 6, -1, 0, 1, 2, 3, 4),
    (6, -1, 0, 1, 2, 3, 4, 5),
)

NIGHT_RULERS = (
    (4, 5, 6, -1, 0, 1, 2, 3),
    (5, 6, -1, 0, 1, 2, 3, 4),
    (6, -1, 0, 1, 2, 3, 4, 5),
    (0, 1, 2, 3, 4, 5, 6, -1),
    (1, 2, 3, 4, 5, 6, -1, 0),
    (2, 3, 4, 5, 6, -1, 0, 1),
    (3, 4, 5, 6, -1, 0, 1, 2),
)

SPECIAL_LAGNA_RATES = {
    "BL": 0.25,
    "HL": 0.5,
    "GL": 1.25,
    "VGL": 15.0,
}

SATURN_PLANET_INDEX = 6
SIGN_LORDS = (
    "Mars",
    "Venus",
    "Mercury",
    "Moon",
    "Sun",
    "Mercury",
    "Venus",
    "Mars",
    "Jupiter",
    "Saturn",
    "Saturn",
    "Jupiter",
)
INDU_FACTORS = {
    "Sun": 30,
    "Moon": 16,
    "Mars": 6,
    "Mercury": 8,
    "Jupiter": 10,
    "Venus": 12,
    "Saturn": 1,
}
SOLAR_UPAGRAHA_OFFSETS = {
    "Dhuma": lambda sun_longitude: (sun_longitude + 133.0 + (20.0 / 60.0)) % 360.0,
    "Vyatipaata": lambda sun_longitude: (360.0 - ((sun_longitude + 133.0 + (20.0 / 60.0)) % 360.0)) % 360.0,
    "Parivesha": lambda sun_longitude: ((360.0 - ((sun_longitude + 133.0 + (20.0 / 60.0)) % 360.0)) + 180.0) % 360.0,
    "Indrachaapa": lambda sun_longitude: (
        360.0
        - (((360.0 - ((sun_longitude + 133.0 + (20.0 / 60.0)) % 360.0)) + 180.0) % 360.0)
    ) % 360.0,
    "Upaketu": lambda sun_longitude: (sun_longitude - 30.0) % 360.0,
}
SEGMENT_UPAGRAHA_RULES = (
    ("Kaala", 0, "middle"),
    ("Mrityu", 2, "middle"),
    ("Artha Praharaka", 3, "middle"),
    ("Yama Ghantaka", 4, "middle"),
    ("Gulika", 6, "begin"),
    ("Maandi", 6, "middle"),
)


@dataclass(frozen=True, slots=True)
class BirthInterval:
    start_at: datetime
    end_at: datetime
    is_night: bool


def decimal_hours(value: datetime | time) -> float:
    if isinstance(value, datetime):
        moment = value.timetz()
    else:
        moment = value
    return (
        moment.hour
        + (moment.minute / 60.0)
        + (moment.second / 3600.0)
        + (moment.microsecond / 3_600_000_000.0)
    )


def weekday_to_sunday_first(py_weekday: int) -> int:
    return (py_weekday + 1) % 7


def compute_special_lagna_longitude(
    *,
    sunrise_sun_longitude: float,
    birth_time_hours: float,
    sunrise_time_hours: float,
    rate_factor: float,
) -> float:
    return (sunrise_sun_longitude + ((birth_time_hours - sunrise_time_hours) * 60.0 * rate_factor)) % 360.0


def count_rasis(from_rasi: int, to_rasi: int, *, direction: int = 1) -> int:
    if direction == 1:
        return ((to_rasi + 12 - from_rasi) % 12) + 1
    return ((from_rasi + 12 - to_rasi) % 12) + 1


def resolve_birth_interval(
    *,
    birth_at: datetime,
    sunrise_at: datetime,
    sunset_at: datetime,
    previous_sunset_at: datetime,
    next_sunrise_at: datetime,
) -> BirthInterval:
    if birth_at < sunrise_at:
        return BirthInterval(
            start_at=previous_sunset_at,
            end_at=sunrise_at,
            is_night=True,
        )
    if birth_at >= sunset_at:
        return BirthInterval(
            start_at=sunset_at,
            end_at=next_sunrise_at,
            is_night=True,
        )
    return BirthInterval(
        start_at=sunrise_at,
        end_at=sunset_at,
        is_night=False,
    )


def compute_saturn_upagraha_time(
    *,
    birth_at: datetime,
    sunrise_at: datetime,
    sunset_at: datetime,
    previous_sunset_at: datetime,
    next_sunrise_at: datetime,
    weekday_index: int,
    upagraha_part: str,
) -> datetime:
    return compute_segment_upagraha_time(
        birth_at=birth_at,
        sunrise_at=sunrise_at,
        sunset_at=sunset_at,
        previous_sunset_at=previous_sunset_at,
        next_sunrise_at=next_sunrise_at,
        weekday_index=weekday_index,
        planet_index=SATURN_PLANET_INDEX,
        upagraha_part=upagraha_part,
    )


def compute_segment_upagraha_time(
    *,
    birth_at: datetime,
    sunrise_at: datetime,
    sunset_at: datetime,
    previous_sunset_at: datetime,
    next_sunrise_at: datetime,
    weekday_index: int,
    planet_index: int,
    upagraha_part: str,
) -> datetime:
    interval = resolve_birth_interval(
        birth_at=birth_at,
        sunrise_at=sunrise_at,
        sunset_at=sunset_at,
        previous_sunset_at=previous_sunset_at,
        next_sunrise_at=next_sunrise_at,
    )
    rulers = NIGHT_RULERS if interval.is_night else DAY_RULERS
    segment_index = rulers[weekday_index].index(planet_index)
    segment_duration = (interval.end_at - interval.start_at) / 8
    event_at = interval.start_at + (segment_duration * segment_index)
    if upagraha_part.casefold() == "middle":
        event_at += segment_duration / 2
    return event_at


def compute_solar_upagraha_longitudes(sun_longitude: float) -> dict[str, float]:
    return {
        name: resolver(sun_longitude)
        for name, resolver in SOLAR_UPAGRAHA_OFFSETS.items()
    }


def compute_pranapada_longitude(
    *,
    sun_longitude: float,
    birth_time_hours: float,
    sunrise_time_hours: float,
) -> float:
    elapsed_minutes = (birth_time_hours - sunrise_time_hours) * 60.0
    base_longitude = (sun_longitude + (elapsed_minutes * 5.0)) % 360.0
    sign_index = int((sun_longitude % 360.0) // 30.0)
    if sign_index in (1, 4, 7, 10):
        base_longitude += 240.0
    elif sign_index in (2, 5, 8, 11):
        base_longitude += 120.0
    return base_longitude % 360.0


def compute_sree_lagna_longitude(*, moon_longitude: float, ascendant_longitude: float) -> float:
    nakshatra_span = 360.0 / 27.0
    moon_remainder = moon_longitude % nakshatra_span
    return (ascendant_longitude + (moon_remainder * 27.0)) % 360.0


def compute_indu_lagna_longitude(*, moon_longitude: float, ascendant_longitude: float) -> float:
    moon_sign = int((moon_longitude % 360.0) // 30.0)
    asc_sign = int((ascendant_longitude % 360.0) // 30.0)
    ninth_lord = SIGN_LORDS[(asc_sign + 8) % 12]
    ninth_lord_from_moon = SIGN_LORDS[(moon_sign + 8) % 12]
    total = (INDU_FACTORS[ninth_lord] + INDU_FACTORS[ninth_lord_from_moon]) % 12
    if total == 0:
        total = 12
    target_sign = (moon_sign + total - 1) % 12
    moon_degree = moon_longitude % 30.0
    return (target_sign * 30.0) + moon_degree


def compute_kunda_lagna_longitude(ascendant_longitude: float) -> float:
    return (ascendant_longitude * 81.0) % 360.0


def compute_yogi_longitude(*, sun_longitude: float, moon_longitude: float) -> float:
    return (sun_longitude + moon_longitude + 93.0 + (20.0 / 60.0)) % 360.0


def compute_avayogi_longitude(yogi_longitude: float) -> float:
    return (yogi_longitude + 186.0 + (40.0 / 60.0)) % 360.0


def compute_varnada_lagna_longitude(
    *,
    ascendant_longitude: float,
    hora_lagna_longitude: float,
) -> float:
    lagna_sign = int((ascendant_longitude % 360.0) // 30.0)
    lagna_degree = ascendant_longitude % 30.0
    hora_sign = int((hora_lagna_longitude % 360.0) // 30.0)

    lagna_is_odd = lagna_sign in (0, 2, 4, 6, 8, 10)
    hora_is_odd = hora_sign in (0, 2, 4, 6, 8, 10)

    count1 = count_rasis(0, lagna_sign, direction=1) if lagna_is_odd else count_rasis(11, lagna_sign, direction=-1)
    count2 = count_rasis(0, hora_sign, direction=1) if hora_is_odd else count_rasis(11, hora_sign, direction=-1)
    if hora_is_odd == lagna_is_odd:
        count = (count1 + count2) % 12
    else:
        count = abs(count1 - count2) % 12
    if lagna_is_odd:
        target_sign = (count_rasis(1, count, direction=1) - 1) % 12
    else:
        target_sign = (count_rasis(12, count, direction=-1) - 1) % 12
    return (target_sign * 30.0) + lagna_degree
