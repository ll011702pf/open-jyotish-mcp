from __future__ import annotations

from dataclasses import dataclass
import math

import swisseph as swe

from open_jyotish.domain.enums.ayanamsha import AyanamshaId
from open_jyotish.domain.models.calculation_profile import CalculationProfile
from open_jyotish.domain.models.chart_result import PlanetPosition
from open_jyotish.domain.models.chart_result import VargaChart
from open_jyotish.domain.rules.dignity import resolve_planet_dignity
from open_jyotish.domain.rules.panchanga import PanchangaValues
from open_jyotish.domain.rules.panchanga import compute_panchanga
from open_jyotish.domain.rules.vargas import VARGA_FACTORS


SIGN_NAMES = (
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

NAKSHATRA_NAMES = (
    "Ashwini",
    "Bharani",
    "Krittika",
    "Rohini",
    "Mrigashirsha",
    "Ardra",
    "Punarvasu",
    "Pushya",
    "Ashlesha",
    "Magha",
    "Purva Phalguni",
    "Uttara Phalguni",
    "Hasta",
    "Chitra",
    "Swati",
    "Vishakha",
    "Anuradha",
    "Jyeshtha",
    "Mula",
    "Purva Ashadha",
    "Uttara Ashadha",
    "Shravana",
    "Dhanishta",
    "Shatabhisha",
    "Purva Bhadrapada",
    "Uttara Bhadrapada",
    "Revati",
)

NAKSHATRA_LORD_CYCLE = (
    "Ketu",
    "Venus",
    "Sun",
    "Moon",
    "Mars",
    "Rahu",
    "Jupiter",
    "Saturn",
    "Mercury",
)

CLASSICAL_PLANET_DEFS = (
    ("Sun", swe.SUN),
    ("Moon", swe.MOON),
    ("Mars", swe.MARS),
    ("Mercury", swe.MERCURY),
    ("Jupiter", swe.JUPITER),
    ("Venus", swe.VENUS),
    ("Saturn", swe.SATURN),
)

OUTER_PLANET_DEFS = (
    ("Uranus", swe.URANUS),
    ("Neptune", swe.NEPTUNE),
    ("Pluto", swe.PLUTO),
)

AYANAMSHA_MAP = {
    AyanamshaId.ALDEBARAN_15TAU: swe.SIDM_ALDEBARAN_15TAU,
    AyanamshaId.ARYABHATA: swe.SIDM_ARYABHATA,
    AyanamshaId.ARYABHATA_522: swe.SIDM_ARYABHATA_522,
    AyanamshaId.ARYABHATA_MSUN: swe.SIDM_ARYABHATA_MSUN,
    AyanamshaId.B1950: swe.SIDM_B1950,
    AyanamshaId.BABYL_BRITTON: swe.SIDM_BABYL_BRITTON,
    AyanamshaId.BABYL_ETPSC: swe.SIDM_BABYL_ETPSC,
    AyanamshaId.BABYL_HUBER: swe.SIDM_BABYL_HUBER,
    AyanamshaId.BABYL_KUGLER1: swe.SIDM_BABYL_KUGLER1,
    AyanamshaId.BABYL_KUGLER2: swe.SIDM_BABYL_KUGLER2,
    AyanamshaId.BABYL_KUGLER3: swe.SIDM_BABYL_KUGLER3,
    AyanamshaId.DELUCE: swe.SIDM_DELUCE,
    AyanamshaId.DJWHAL_KHUL: swe.SIDM_DJWHAL_KHUL,
    AyanamshaId.FAGAN_BRADLEY: swe.SIDM_FAGAN_BRADLEY,
    AyanamshaId.GALALIGN_MARDYKS: swe.SIDM_GALALIGN_MARDYKS,
    AyanamshaId.GALCENT_0SAG: swe.SIDM_GALCENT_0SAG,
    AyanamshaId.GALCENT_COCHRANE: swe.SIDM_GALCENT_COCHRANE,
    AyanamshaId.GALCENT_MULA_WILHELM: swe.SIDM_GALCENT_MULA_WILHELM,
    AyanamshaId.GALCENT_RGILBRAND: swe.SIDM_GALCENT_RGILBRAND,
    AyanamshaId.GALEQU_FIORENZA: swe.SIDM_GALEQU_FIORENZA,
    AyanamshaId.GALEQU_IAU1958: swe.SIDM_GALEQU_IAU1958,
    AyanamshaId.GALEQU_MULA: swe.SIDM_GALEQU_MULA,
    AyanamshaId.GALEQU_TRUE: swe.SIDM_GALEQU_TRUE,
    AyanamshaId.HIPPARCHOS: swe.SIDM_HIPPARCHOS,
    AyanamshaId.J1900: swe.SIDM_J1900,
    AyanamshaId.J2000: swe.SIDM_J2000,
    AyanamshaId.JN_BHASIN: swe.SIDM_JN_BHASIN,
    AyanamshaId.LAHIRI: swe.SIDM_LAHIRI,
    AyanamshaId.LAHIRI_1940: swe.SIDM_LAHIRI_1940,
    AyanamshaId.LAHIRI_VP285: swe.SIDM_LAHIRI_VP285,
    AyanamshaId.LAHIRI_ICRC: swe.SIDM_LAHIRI_ICRC,
    AyanamshaId.RAMAN: swe.SIDM_RAMAN,
    AyanamshaId.SASSANIAN: swe.SIDM_SASSANIAN,
    AyanamshaId.SS_CITRA: swe.SIDM_SS_CITRA,
    AyanamshaId.SS_REVATI: swe.SIDM_SS_REVATI,
    AyanamshaId.KRISHNAMURTI: swe.SIDM_KRISHNAMURTI,
    AyanamshaId.KRISHNAMURTI_VP291: swe.SIDM_KRISHNAMURTI_VP291,
    AyanamshaId.YUKTESHWAR: swe.SIDM_YUKTESHWAR,
    AyanamshaId.SURYASIDDHANTA: swe.SIDM_SURYASIDDHANTA,
    AyanamshaId.SURYASIDDHANTA_MSUN: swe.SIDM_SURYASIDDHANTA_MSUN,
    AyanamshaId.TRUE_CITRA: swe.SIDM_TRUE_CITRA,
    AyanamshaId.TRUE_MULA: swe.SIDM_TRUE_MULA,
    AyanamshaId.TRUE_PUSHYA: swe.SIDM_TRUE_PUSHYA,
    AyanamshaId.TRUE_REVATI: swe.SIDM_TRUE_REVATI,
    AyanamshaId.TRUE_SHEORAN: swe.SIDM_TRUE_SHEORAN,
    AyanamshaId.USHASHASHI: swe.SIDM_USHASHASHI,
    AyanamshaId.VALENS_MOON: swe.SIDM_VALENS_MOON,
}

HOUSE_SYSTEM_MAP = {
    "whole_sign": b"W",
}

ODD_SIGNS = {0, 2, 4, 6, 8, 10}
EVEN_SIGNS = {1, 3, 5, 7, 9, 11}
MOVABLE_SIGNS = {0, 3, 6, 9}
FIXED_SIGNS = {1, 4, 7, 10}
DUAL_SIGNS = {2, 5, 8, 11}
FIRE_SIGNS = {0, 4, 8}
EARTH_SIGNS = {1, 5, 9}
AIR_SIGNS = {2, 6, 10}
WATER_SIGNS = {3, 7, 11}
PANCHAMSA_ODD_SIGNS = (0, 10, 8, 2, 6)
PANCHAMSA_EVEN_SIGNS = (1, 5, 11, 9, 7)


@dataclass(slots=True)
class EphemerisChartResult:
    ayanamsha_value: float
    lagna_longitude: float
    houses: list[float]
    planets: list[PlanetPosition]


class SwissEphemerisAdapter:
    def calculate_rashi_chart(
        self,
        jd_ut: float,
        latitude: float,
        longitude: float,
        profile: CalculationProfile,
    ) -> EphemerisChartResult:
        self._set_sidereal_mode(profile)
        flags = swe.FLG_SWIEPH | swe.FLG_SPEED | swe.FLG_SIDEREAL
        house_system = HOUSE_SYSTEM_MAP.get(profile.house_system, b"W")
        cusps, ascmc = swe.houses_ex(jd_ut, latitude, longitude, house_system, swe.FLG_SIDEREAL)
        lagna_longitude = normalize_degrees(ascmc[0])
        lagna_sign_index = degrees_to_sign_index(lagna_longitude)

        planets: list[PlanetPosition] = []
        for planet_name, planet_id in self._planet_defs(profile):
            xx, _ = swe.calc_ut(jd_ut, planet_id, flags)
            longitude_sidereal = normalize_degrees(xx[0])
            planets.append(
                build_planet_position(
                    planet_name=planet_name,
                    longitude_sidereal=longitude_sidereal,
                    speed=xx[3],
                    lagna_sign_index=lagna_sign_index,
                )
            )

        node_id = swe.TRUE_NODE if profile.node_mode == "true" else swe.MEAN_NODE
        rahu_longitude, node_speed = self._calculate_sidereal_node(
            jd_ut=jd_ut,
            node_id=node_id,
            flags=flags,
        )
        ketu_longitude = normalize_degrees(rahu_longitude + 180.0)
        planets.append(
            build_planet_position(
                planet_name="Rahu",
                longitude_sidereal=rahu_longitude,
                speed=node_speed,
                lagna_sign_index=lagna_sign_index,
            )
        )
        planets.append(
            build_planet_position(
                planet_name="Ketu",
                longitude_sidereal=ketu_longitude,
                speed=node_speed,
                lagna_sign_index=lagna_sign_index,
            )
        )

        ayanamsha_value = swe.get_ayanamsa_ut(jd_ut)
        return EphemerisChartResult(
            ayanamsha_value=ayanamsha_value,
            lagna_longitude=lagna_longitude,
            houses=[normalize_degrees(cusp) for cusp in cusps],
            planets=planets,
        )

    def build_varga_chart(
        self,
        *,
        name: str,
        d1_planets: list[PlanetPosition],
        lagna_longitude: float,
    ) -> VargaChart:
        factor = VARGA_FACTORS[name]
        varga_lagna = self._project_varga_longitude(
            longitude=lagna_longitude,
            varga_name=name,
            factor=factor,
        )
        varga_lagna_sign_index = degrees_to_sign_index(varga_lagna)
        varga_planets = [
            build_planet_position(
                planet_name=planet.planet,
                longitude_sidereal=self._project_varga_longitude(
                    longitude=planet.longitude_sidereal,
                    varga_name=name,
                    factor=factor,
                ),
                speed=-1.0 if planet.retrograde else 1.0,
                lagna_sign_index=varga_lagna_sign_index,
            )
            for planet in d1_planets
        ]
        return VargaChart(
            name=name,
            lagna_longitude=varga_lagna,
            planets=varga_planets,
        )

    def build_moon_chart(self, *, d1_planets: list[PlanetPosition]) -> VargaChart:
        moon = next(planet for planet in d1_planets if planet.planet == "Moon")
        moon_sign_index = degrees_to_sign_index(moon.longitude_sidereal)
        planets = [
            build_planet_position(
                planet_name=planet.planet,
                longitude_sidereal=planet.longitude_sidereal,
                speed=-1.0 if planet.retrograde else 1.0,
                lagna_sign_index=moon_sign_index,
            )
            for planet in d1_planets
        ]
        return VargaChart(
            name="Moon",
            lagna_longitude=moon.longitude_sidereal,
            planets=planets,
        )

    def build_bhava_chart(
        self,
        *,
        d1_planets: list[PlanetPosition],
        lagna_longitude: float,
        houses: list[float],
    ) -> VargaChart:
        planets = [
            planet.model_copy(
                update={
                    "house": house_from_cusps(
                        longitude=planet.longitude_sidereal,
                        cusps=houses,
                    )
                }
            )
            for planet in d1_planets
        ]
        return VargaChart(
            name="Bhava",
            lagna_longitude=lagna_longitude,
            planets=planets,
        )

    def calculate_panchanga(
        self,
        *,
        jd_ut: float,
        profile: CalculationProfile,
        weekday_index: int,
    ) -> PanchangaValues:
        self._set_sidereal_mode(profile)
        flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        sun_xx, _ = swe.calc_ut(jd_ut, swe.SUN, flags)
        moon_xx, _ = swe.calc_ut(jd_ut, swe.MOON, flags)
        return compute_panchanga(
            sun_longitude=normalize_degrees(sun_xx[0]),
            moon_longitude=normalize_degrees(moon_xx[0]),
            weekday_index=weekday_index,
        )

    def calculate_sidereal_time_hours(self, *, jd_ut: float, longitude: float) -> float:
        return (float(swe.sidtime(jd_ut)) + (longitude / 15.0)) % 24.0

    def calculate_sunrise_sunset(
        self,
        *,
        jd_ut: float,
        latitude: float,
        longitude: float,
        altitude_m: float = 0.0,
    ) -> tuple[float | None, float | None]:
        flags = swe.FLG_SWIEPH
        geopos = (longitude, latitude, altitude_m)
        sunrise_jd = None
        sunset_jd = None
        try:
            rise_res, rise_times = swe.rise_trans(
                jd_ut,
                swe.SUN,
                swe.CALC_RISE | swe.BIT_DISC_CENTER,
                geopos,
                0.0,
                0.0,
                flags,
            )
            if rise_res == 0:
                sunrise_jd = float(rise_times[0])
        except swe.Error:
            sunrise_jd = None
        try:
            set_res, set_times = swe.rise_trans(
                jd_ut,
                swe.SUN,
                swe.CALC_SET | swe.BIT_DISC_CENTER,
                geopos,
                0.0,
                0.0,
                flags,
            )
            if set_res == 0:
                sunset_jd = float(set_times[0])
        except swe.Error:
            sunset_jd = None
        return sunrise_jd, sunset_jd

    def calculate_body_longitude(
        self,
        *,
        jd_ut: float,
        body_id: int,
        profile: CalculationProfile,
    ) -> float:
        self._set_sidereal_mode(profile)
        flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        xx, _ = swe.calc_ut(jd_ut, body_id, flags)
        return normalize_degrees(xx[0])

    def calculate_lagna_longitude(
        self,
        *,
        jd_ut: float,
        latitude: float,
        longitude: float,
        profile: CalculationProfile,
    ) -> float:
        self._set_sidereal_mode(profile)
        house_system = HOUSE_SYSTEM_MAP.get(profile.house_system, b"W")
        _, ascmc = swe.houses_ex(jd_ut, latitude, longitude, house_system, swe.FLG_SIDEREAL)
        return normalize_degrees(ascmc[0])

    def _project_varga_longitude(
        self,
        *,
        longitude: float,
        varga_name: str,
        factor: int,
    ) -> float:
        normalized = normalize_degrees(longitude)
        sign_index = degrees_to_sign_index(normalized)
        degree_in_sign = normalized - (sign_index * 30.0)
        if varga_name == "D30":
            projected_degree = (degree_in_sign * factor) % 30.0
            target_sign = self._resolve_d30_sign(
                sign_index=sign_index,
                degree_in_sign=degree_in_sign,
            )
            return normalize_degrees((target_sign * 30.0) + projected_degree)
        division_size = 30.0 / factor
        division_index = min(factor - 1, int(degree_in_sign // division_size))
        projected_degree = (degree_in_sign * factor) % 30.0
        target_sign = self._resolve_varga_sign(
            sign_index=sign_index,
            division_index=division_index,
            varga_name=varga_name,
        )
        return normalize_degrees((target_sign * 30.0) + projected_degree)

    def _resolve_varga_sign(
        self,
        *,
        sign_index: int,
        division_index: int,
        varga_name: str,
    ) -> int:
        if varga_name == "D1":
            return sign_index
        if varga_name == "D2":
            sun_hora = (sign_index in ODD_SIGNS and division_index == 0) or (
                sign_index in EVEN_SIGNS and division_index == 1
            )
            return 4 if sun_hora else 3
        if varga_name == "D3":
            return (sign_index + (division_index * 4)) % 12
        if varga_name == "D4":
            return (sign_index + (division_index * 3)) % 12
        if varga_name == "D5":
            source = PANCHAMSA_ODD_SIGNS if sign_index in ODD_SIGNS else PANCHAMSA_EVEN_SIGNS
            return source[division_index]
        if varga_name == "D6":
            return division_index if sign_index in ODD_SIGNS else (division_index + 6) % 12
        if varga_name == "D7":
            start_sign = sign_index if sign_index in ODD_SIGNS else (sign_index + 6) % 12
            return (start_sign + division_index) % 12
        if varga_name == "D8":
            if sign_index in MOVABLE_SIGNS:
                start_sign = 0
            elif sign_index in FIXED_SIGNS:
                start_sign = 8
            else:
                start_sign = 4
            return (start_sign + division_index) % 12
        if varga_name == "D9":
            if sign_index in MOVABLE_SIGNS:
                start_sign = sign_index
            elif sign_index in FIXED_SIGNS:
                start_sign = (sign_index + 8) % 12
            else:
                start_sign = (sign_index + 4) % 12
            return (start_sign + division_index) % 12
        if varga_name == "D10":
            start_sign = sign_index if sign_index in ODD_SIGNS else (sign_index + 8) % 12
            return (start_sign + division_index) % 12
        if varga_name == "D11":
            return (12 - sign_index + division_index) % 12
        if varga_name == "D12":
            return (sign_index + division_index) % 12
        if varga_name == "D16":
            if sign_index in MOVABLE_SIGNS:
                start_sign = 0
            elif sign_index in FIXED_SIGNS:
                start_sign = 4
            else:
                start_sign = 8
            return (start_sign + division_index) % 12
        if varga_name == "D20":
            if sign_index in MOVABLE_SIGNS:
                start_sign = 0
            elif sign_index in FIXED_SIGNS:
                start_sign = 8
            else:
                start_sign = 4
            return (start_sign + division_index) % 12
        if varga_name == "D24":
            start_sign = 4 if sign_index in ODD_SIGNS else 3
            return (start_sign + division_index) % 12
        if varga_name == "D27":
            if sign_index in FIRE_SIGNS:
                start_sign = 0
            elif sign_index in EARTH_SIGNS:
                start_sign = 3
            elif sign_index in AIR_SIGNS:
                start_sign = 6
            else:
                start_sign = 9
            return (start_sign + division_index) % 12
        if varga_name == "D40":
            start_sign = 0 if sign_index in ODD_SIGNS else 6
            return (start_sign + division_index) % 12
        if varga_name == "D45":
            if sign_index in MOVABLE_SIGNS:
                start_sign = 0
            elif sign_index in FIXED_SIGNS:
                start_sign = 4
            else:
                start_sign = 8
            return (start_sign + division_index) % 12
        if varga_name == "D60":
            return (sign_index + division_index) % 12
        raise ValueError(f"unsupported varga: {varga_name}")

    def _resolve_d30_sign(
        self,
        *,
        sign_index: int,
        degree_in_sign: float,
    ) -> int:
        if sign_index in ODD_SIGNS:
            if degree_in_sign <= 5.0:
                return 0
            if degree_in_sign <= 10.0:
                return 10
            if degree_in_sign <= 18.0:
                return 8
            if degree_in_sign <= 25.0:
                return 2
            return 6

        if degree_in_sign <= 5.0:
            return 1
        if degree_in_sign <= 12.0:
            return 5
        if degree_in_sign <= 20.0:
            return 11
        if degree_in_sign <= 25.0:
            return 9
        return 7

    def _set_sidereal_mode(self, profile: CalculationProfile) -> None:
        if profile.ayanamsha_id == AyanamshaId.CUSTOM:
            if profile.custom_ayanamsha_t0_jd is None or profile.custom_ayanamsha_value is None:
                raise ValueError("custom ayanamsha requires t0 and ayanamsha value")
            sid_mode = swe.SIDM_USER
            if profile.custom_ayanamsha_is_ut:
                sid_mode |= swe.SIDBIT_USER_UT
            swe.set_sid_mode(
                sid_mode,
                profile.custom_ayanamsha_t0_jd,
                profile.custom_ayanamsha_value,
            )
            return

        sid_mode = AYANAMSHA_MAP.get(profile.ayanamsha_id)
        if sid_mode is None:
            raise ValueError(f"unsupported ayanamsha: {profile.ayanamsha_id}")
        swe.set_sid_mode(sid_mode)

    def _planet_defs(self, profile: CalculationProfile) -> tuple[tuple[str, int], ...]:
        if profile.include_outer_planets:
            return (*CLASSICAL_PLANET_DEFS, *OUTER_PLANET_DEFS)
        return CLASSICAL_PLANET_DEFS

    def _calculate_sidereal_node(
        self,
        *,
        jd_ut: float,
        node_id: int,
        flags: int,
    ) -> tuple[float, float]:
        try:
            node_xx, _ = swe.calc_ut(jd_ut, node_id, flags)
            return normalize_degrees(node_xx[0]), node_xx[3]
        except swe.Error:
            # Some sidereal mode + true-node combinations fail inside pyswisseph.
            # Fall back to a tropical node position and apply the current ayanamsha.
            tropical_flags = flags & ~swe.FLG_SIDEREAL
            node_xx, _ = swe.calc_ut(jd_ut, node_id, tropical_flags)
            ayanamsha_value = swe.get_ayanamsa_ut(jd_ut)
            return normalize_degrees(node_xx[0] - ayanamsha_value), node_xx[3]


def build_planet_position(
    planet_name: str,
    longitude_sidereal: float,
    speed: float,
    lagna_sign_index: int,
) -> PlanetPosition:
    sign_index = degrees_to_sign_index(longitude_sidereal)
    sign_start = sign_index * 30.0
    degree_in_sign = longitude_sidereal - sign_start
    house = ((sign_index - lagna_sign_index) % 12) + 1

    nakshatra_span = 360.0 / 27.0
    pada_span = nakshatra_span / 4.0
    nakshatra_index = int(longitude_sidereal // nakshatra_span)
    nakshatra_offset = longitude_sidereal - (nakshatra_index * nakshatra_span)
    pada = int(nakshatra_offset // pada_span) + 1

    return PlanetPosition(
        planet=planet_name,
        longitude_sidereal=longitude_sidereal,
        sign=SIGN_NAMES[sign_index],
        degree_in_sign=degree_in_sign,
        nakshatra=NAKSHATRA_NAMES[nakshatra_index],
        nakshatra_lord=NAKSHATRA_LORD_CYCLE[nakshatra_index % len(NAKSHATRA_LORD_CYCLE)],
        pada=min(pada, 4),
        house=house,
        retrograde=math.isfinite(speed) and speed < 0,
        dignity=resolve_planet_dignity(planet_name, SIGN_NAMES[sign_index]),
        speed_value=float(speed) if math.isfinite(speed) else None,
    )


def normalize_degrees(value: float) -> float:
    return value % 360.0


def degrees_to_sign_index(value: float) -> int:
    return int(normalize_degrees(value) // 30.0)


def house_from_cusps(*, longitude: float, cusps: list[float]) -> int:
    if len(cusps) != 12:
        return 1
    normalized_longitude = normalize_degrees(longitude)
    normalized_cusps = [normalize_degrees(cusp) for cusp in cusps]
    for index, cusp in enumerate(normalized_cusps):
        next_cusp = normalized_cusps[(index + 1) % 12]
        span = (next_cusp - cusp) % 360.0
        offset = (normalized_longitude - cusp) % 360.0
        if offset < span or math.isclose(offset, 0.0):
            return index + 1
    return 12
