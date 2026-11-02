from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from datetime import datetime
from datetime import time
from datetime import timezone
from uuid import uuid4

from open_jyotish.domain.models.birth_data import BirthData
from open_jyotish.domain.models.calculation_profile import CalculationProfile
from open_jyotish.domain.models.chart_result import ChartResult
from open_jyotish.domain.models.chart_result import PanchangaDetails
from open_jyotish.domain.models.chart_result import SolarContext
from open_jyotish.domain.models.chart_result import TransitSnapshot
from open_jyotish.domain.models.chart_result import VargaChart
from open_jyotish.domain.rules.arudha import build_arudha_longitudes
from open_jyotish.domain.rules.argala import build_argala_entries
from open_jyotish.domain.rules.aspects import build_aspects
from open_jyotish.domain.rules.ashtakavarga import compute_ashtakavarga
from open_jyotish.domain.rules.avasthas import compute_planetary_states
from open_jyotish.domain.rules.chara_karakas import compute_chara_karakas
from open_jyotish.domain.rules.auxiliary_points import compute_avayogi_longitude
from open_jyotish.domain.rules.auxiliary_points import compute_indu_lagna_longitude
from open_jyotish.domain.rules.auxiliary_points import compute_kunda_lagna_longitude
from open_jyotish.domain.rules.auxiliary_points import compute_pranapada_longitude
from open_jyotish.domain.rules.auxiliary_points import compute_segment_upagraha_time
from open_jyotish.domain.rules.auxiliary_points import compute_special_lagna_longitude
from open_jyotish.domain.rules.auxiliary_points import compute_solar_upagraha_longitudes
from open_jyotish.domain.rules.auxiliary_points import compute_sree_lagna_longitude
from open_jyotish.domain.rules.auxiliary_points import compute_varnada_lagna_longitude
from open_jyotish.domain.rules.auxiliary_points import compute_yogi_longitude
from open_jyotish.domain.rules.auxiliary_points import decimal_hours
from open_jyotish.domain.rules.auxiliary_points import SEGMENT_UPAGRAHA_RULES
from open_jyotish.domain.rules.auxiliary_points import SPECIAL_LAGNA_RATES
from open_jyotish.domain.rules.auxiliary_points import weekday_to_sunday_first
from open_jyotish.domain.rules.relationships import build_planet_relationships
from open_jyotish.domain.rules.doshas import detect_doshas
from open_jyotish.domain.rules.strengths import compute_core_strengths
from open_jyotish.domain.rules.transits import build_transit_entries
from open_jyotish.domain.rules.transit_ashtakavarga_overlay import build_transit_ashtakavarga_overlay
from open_jyotish.domain.rules.yogas import detect_yogas
from open_jyotish.domain.rules.varga_quality import compute_varga_quality_profiles
from open_jyotish.domain.rules.vargas import VARGA_FACTORS
from open_jyotish.domain.services.vimshottari_dasha import VimshottariDashaService
from open_jyotish.infrastructure.ephemeris.swiss_ephemeris_adapter import SwissEphemerisAdapter
from open_jyotish.infrastructure.ephemeris.swiss_ephemeris_adapter import build_planet_position
from open_jyotish.infrastructure.timezone.timezone_service import TimezoneService


@dataclass(slots=True)
class ChartCalculationService:
    timezone_service: TimezoneService
    ephemeris_adapter: SwissEphemerisAdapter
    dasha_service: VimshottariDashaService | None = None

    def calculate_chart(
        self,
        birth_data: BirthData,
        profile: CalculationProfile,
        transit_as_of: datetime | None = None,
    ) -> ChartResult:
        if self.dasha_service is None:
            self.dasha_service = VimshottariDashaService()

        birth_utc = self.timezone_service.to_utc_datetime(birth_data)
        birth_local = self.timezone_service.to_local_timezone(
            birth_utc,
            birth_data.timezone,
        )
        jd_ut = self.timezone_service.to_julian_day_ut(birth_data)
        ephemeris_result = self.ephemeris_adapter.calculate_rashi_chart(
            jd_ut=jd_ut,
            latitude=birth_data.latitude,
            longitude=birth_data.longitude,
            profile=profile,
        )
        vargas = self._build_vargas(
            profile=profile,
            lagna_longitude=ephemeris_result.lagna_longitude,
            d1_planets=ephemeris_result.planets,
        )
        moon_chart = self.ephemeris_adapter.build_moon_chart(
            d1_planets=ephemeris_result.planets,
        )
        bhava_chart = self.ephemeris_adapter.build_bhava_chart(
            d1_planets=ephemeris_result.planets,
            lagna_longitude=ephemeris_result.lagna_longitude,
            houses=ephemeris_result.houses,
        )
        moon = next(planet for planet in ephemeris_result.planets if planet.planet == "Moon")
        dasha_periods = self.dasha_service.build_mahadasha_periods(
            birth_utc=birth_utc,
            moon=moon,
        )
        antardasha_periods = self.dasha_service.build_antardasha_periods(
            mahadasha_periods=dasha_periods,
        )
        panchanga_values = self.ephemeris_adapter.calculate_panchanga(
            jd_ut=jd_ut,
            profile=profile,
            weekday_index=birth_data.birth_date.weekday(),
        )
        day_start_jd_ut = self.timezone_service.to_julian_day_ut(
            birth_data.model_copy(update={"birth_time": time(0, 0, 0)})
        )
        sunrise_jd_ut, sunset_jd_ut = self.ephemeris_adapter.calculate_sunrise_sunset(
            jd_ut=day_start_jd_ut,
            latitude=birth_data.latitude,
            longitude=birth_data.longitude,
        )
        sidereal_time_hours = self.ephemeris_adapter.calculate_sidereal_time_hours(
            jd_ut=jd_ut,
            longitude=birth_data.longitude,
        )
        solar_context = SolarContext(
            sidereal_time_hours=sidereal_time_hours,
            sidereal_time_text=self._format_hours(sidereal_time_hours),
            sunrise_at=self._local_datetime_or_none(birth_data.timezone, sunrise_jd_ut),
            sunset_at=self._local_datetime_or_none(birth_data.timezone, sunset_jd_ut),
        )
        auxiliary_points = self._build_auxiliary_points(
            birth_data=birth_data,
            profile=profile,
            sunrise_jd_ut=sunrise_jd_ut,
            sunrise_at=solar_context.sunrise_at,
            sunset_at=solar_context.sunset_at,
            lagna_longitude=ephemeris_result.lagna_longitude,
            d1_planets=ephemeris_result.planets,
        )
        quality_vargas = self._build_quality_vargas(
            lagna_longitude=ephemeris_result.lagna_longitude,
            d1_planets=ephemeris_result.planets,
        )
        planet_strengths = compute_core_strengths(
            planets=ephemeris_result.planets,
            houses=ephemeris_result.houses,
            varga_charts=quality_vargas,
            birth_data=birth_data,
            birth_local=birth_local,
            sunrise_at=solar_context.sunrise_at,
            sunset_at=solar_context.sunset_at,
        )
        ashtakavarga = compute_ashtakavarga(
            planets=ephemeris_result.planets,
            lagna_longitude=ephemeris_result.lagna_longitude,
        )
        varga_quality_profiles = compute_varga_quality_profiles(
            rasi_planets=ephemeris_result.planets,
            varga_charts=quality_vargas,
        )
        chara_karakas = compute_chara_karakas(ephemeris_result.planets)
        planetary_states = compute_planetary_states(
            planets=ephemeris_result.planets,
            birth_local=birth_local,
        )
        yogas = detect_yogas(
            planets=ephemeris_result.planets,
            lagna_longitude=ephemeris_result.lagna_longitude,
        )
        doshas = detect_doshas(
            planets=ephemeris_result.planets,
            lagna_longitude=ephemeris_result.lagna_longitude,
        )
        planet_relationships = build_planet_relationships(
            planets=ephemeris_result.planets,
            lagna_longitude=ephemeris_result.lagna_longitude,
        )
        aspects = build_aspects(
            planets=ephemeris_result.planets,
            lagna_longitude=ephemeris_result.lagna_longitude,
        )
        argala_entries = build_argala_entries(
            planets=ephemeris_result.planets,
            lagna_longitude=ephemeris_result.lagna_longitude,
            auxiliary_points=auxiliary_points,
        )
        transit_as_of_utc = (
            transit_as_of.astimezone(timezone.utc)
            if transit_as_of is not None and transit_as_of.tzinfo is not None
            else (
                transit_as_of.replace(tzinfo=timezone.utc)
                if transit_as_of is not None
                else datetime.now(timezone.utc)
            )
        )
        transit_jd_ut = self.timezone_service.to_julian_day_ut_from_utc(transit_as_of_utc)
        transit_ephemeris_result = self.ephemeris_adapter.calculate_rashi_chart(
            jd_ut=transit_jd_ut,
            latitude=birth_data.latitude,
            longitude=birth_data.longitude,
            profile=profile,
        )
        transit_snapshot = TransitSnapshot(
            as_of_utc=transit_as_of_utc,
            as_of_local=self.timezone_service.to_local_timezone(transit_as_of_utc, birth_data.timezone),
            timezone=birth_data.timezone,
            transit_lagna_longitude=transit_ephemeris_result.lagna_longitude,
            entries=build_transit_entries(
                natal_planets=ephemeris_result.planets,
                transit_planets=transit_ephemeris_result.planets,
                natal_lagna_longitude=ephemeris_result.lagna_longitude,
            ),
        )
        transit_overlay = build_transit_ashtakavarga_overlay(
            transit_snapshot=transit_snapshot,
            ashtakavarga=ashtakavarga,
        )
        return ChartResult(
            chart_id=str(uuid4()),
            birth_data=birth_data,
            profile=profile,
            jd_ut=jd_ut,
            ayanamsha_value=ephemeris_result.ayanamsha_value,
            lagna_longitude=ephemeris_result.lagna_longitude,
            planets=ephemeris_result.planets,
            houses=ephemeris_result.houses,
            vargas=vargas,
            moon_chart=moon_chart,
            bhava_chart=bhava_chart,
            vimshottari_dasha=dasha_periods,
            vimshottari_antardasha=antardasha_periods,
            panchanga=PanchangaDetails(
                vedic_weekday=panchanga_values.vedic_weekday,
                tithi_name=panchanga_values.tithi_name,
                tithi_number=panchanga_values.tithi_number,
                tithi_progress_percent=panchanga_values.tithi_progress_percent,
                yoga_name=panchanga_values.yoga_name,
                yoga_number=panchanga_values.yoga_number,
                yoga_progress_percent=panchanga_values.yoga_progress_percent,
                karana_name=panchanga_values.karana_name,
                karana_number=panchanga_values.karana_number,
                karana_progress_percent=panchanga_values.karana_progress_percent,
            ),
            solar_context=solar_context,
            auxiliary_points=auxiliary_points,
            planet_strengths=planet_strengths,
            ashtakavarga=ashtakavarga,
            varga_quality_profiles=varga_quality_profiles,
            chara_karakas=chara_karakas,
            planetary_states=planetary_states,
            yogas=yogas,
            doshas=doshas,
            planet_relationships=planet_relationships,
            aspects=aspects,
            argala_entries=argala_entries,
            transit_snapshot=transit_snapshot,
            transit_ashtakavarga_overlay=transit_overlay,
            computed_at=datetime.now(),
        )

    def _build_vargas(
        self,
        *,
        profile: CalculationProfile,
        lagna_longitude: float,
        d1_planets: list,
    ) -> dict[str, VargaChart]:
        requested = set(profile.enabled_vargas)
        requested.add("D1")

        vargas: dict[str, VargaChart] = {
            "D1": VargaChart(
                name="D1",
                lagna_longitude=lagna_longitude,
                planets=d1_planets,
            )
        }

        for varga_name in VARGA_FACTORS:
            if varga_name not in requested:
                continue
            if varga_name == "D1":
                continue
            vargas[varga_name] = self.ephemeris_adapter.build_varga_chart(
                name=varga_name,
                d1_planets=d1_planets,
                lagna_longitude=lagna_longitude,
            )
        return vargas

    def _build_quality_vargas(
        self,
        *,
        lagna_longitude: float,
        d1_planets: list,
    ) -> dict[str, VargaChart]:
        required = {"D1", "D2", "D3", "D4", "D7", "D9", "D10", "D12", "D16", "D20", "D24", "D27", "D30", "D40", "D45", "D60"}
        vargas: dict[str, VargaChart] = {
            "D1": VargaChart(
                name="D1",
                lagna_longitude=lagna_longitude,
                planets=d1_planets,
            )
        }
        for varga_name in VARGA_FACTORS:
            if varga_name == "D1" or varga_name not in required:
                continue
            vargas[varga_name] = self.ephemeris_adapter.build_varga_chart(
                name=varga_name,
                d1_planets=d1_planets,
                lagna_longitude=lagna_longitude,
            )
        return vargas

    def _build_auxiliary_points(
        self,
        *,
        birth_data: BirthData,
        profile: CalculationProfile,
        sunrise_jd_ut: float | None,
        sunrise_at: datetime | None,
        sunset_at: datetime | None,
        lagna_longitude: float,
        d1_planets: list,
    ) -> list:
        arudha_longitudes = build_arudha_longitudes(
            lagna_longitude=lagna_longitude,
            planets=d1_planets,
        )
        lagna_sign_index = int((lagna_longitude % 360.0) // 30.0)
        points = [
            build_planet_position(
                planet_name=name,
                longitude_sidereal=arudha_longitudes[name],
                speed=1.0,
                lagna_sign_index=lagna_sign_index,
            )
            for name in ("AL", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9", "A10", "A11", "A12", "UL")
        ]
        if sunrise_jd_ut is None or sunrise_at is None or sunset_at is None:
            return points

        birth_local = self.timezone_service.to_local_timezone(
            self.timezone_service.to_utc_datetime(birth_data),
            birth_data.timezone,
        )
        d1_planet_map = {planet.planet: planet for planet in d1_planets}
        sun_longitude = d1_planet_map["Sun"].longitude_sidereal
        moon_longitude = d1_planet_map["Moon"].longitude_sidereal
        for name, longitude in compute_solar_upagraha_longitudes(sun_longitude).items():
            points.append(
                build_planet_position(
                    planet_name=name,
                    longitude_sidereal=longitude,
                    speed=1.0,
                    lagna_sign_index=lagna_sign_index,
                )
            )
        sunrise_sun_longitude = self.ephemeris_adapter.calculate_body_longitude(
            jd_ut=sunrise_jd_ut,
            body_id=0,
            profile=profile,
        )
        birth_hours = decimal_hours(birth_local)
        sunrise_hours = decimal_hours(sunrise_at)
        for name, rate_factor in SPECIAL_LAGNA_RATES.items():
            points.append(
                build_planet_position(
                    planet_name=name,
                    longitude_sidereal=compute_special_lagna_longitude(
                        sunrise_sun_longitude=sunrise_sun_longitude,
                        birth_time_hours=birth_hours,
                        sunrise_time_hours=sunrise_hours,
                        rate_factor=rate_factor,
                    ),
                    speed=1.0,
                    lagna_sign_index=lagna_sign_index,
                )
            )
        points.extend(
            [
                build_planet_position(
                    planet_name="Pranapada",
                    longitude_sidereal=compute_pranapada_longitude(
                        sun_longitude=sun_longitude,
                        birth_time_hours=birth_hours,
                        sunrise_time_hours=sunrise_hours,
                    ),
                    speed=1.0,
                    lagna_sign_index=lagna_sign_index,
                ),
                build_planet_position(
                    planet_name="Sree",
                    longitude_sidereal=compute_sree_lagna_longitude(
                        moon_longitude=moon_longitude,
                        ascendant_longitude=lagna_longitude,
                    ),
                    speed=1.0,
                    lagna_sign_index=lagna_sign_index,
                ),
                build_planet_position(
                    planet_name="Indu",
                    longitude_sidereal=compute_indu_lagna_longitude(
                        moon_longitude=moon_longitude,
                        ascendant_longitude=lagna_longitude,
                    ),
                    speed=1.0,
                    lagna_sign_index=lagna_sign_index,
                ),
                build_planet_position(
                    planet_name="Kunda",
                    longitude_sidereal=compute_kunda_lagna_longitude(lagna_longitude),
                    speed=1.0,
                    lagna_sign_index=lagna_sign_index,
                ),
            ]
        )
        yogi_longitude = compute_yogi_longitude(
            sun_longitude=sun_longitude,
            moon_longitude=moon_longitude,
        )
        points.extend(
            [
                build_planet_position(
                    planet_name="Yogi",
                    longitude_sidereal=yogi_longitude,
                    speed=1.0,
                    lagna_sign_index=lagna_sign_index,
                ),
                build_planet_position(
                    planet_name="Avayogi",
                    longitude_sidereal=compute_avayogi_longitude(yogi_longitude),
                    speed=1.0,
                    lagna_sign_index=lagna_sign_index,
                ),
            ]
        )

        previous_sunset_at = self._adjacent_solar_event(
            birth_data=birth_data,
            target_date=birth_data.birth_date.toordinal() - 1,
            event="sunset",
        )
        next_sunrise_at = self._adjacent_solar_event(
            birth_data=birth_data,
            target_date=birth_data.birth_date.toordinal() + 1,
            event="sunrise",
        )
        if previous_sunset_at is None or next_sunrise_at is None:
            return points

        weekday_index = weekday_to_sunday_first(birth_data.birth_date.weekday())
        event_points: dict[str, float] = {}
        for name, planet_index, part in SEGMENT_UPAGRAHA_RULES:
            event_at = compute_segment_upagraha_time(
                birth_at=birth_local,
                sunrise_at=sunrise_at,
                sunset_at=sunset_at,
                previous_sunset_at=previous_sunset_at,
                next_sunrise_at=next_sunrise_at,
                weekday_index=weekday_index,
                planet_index=planet_index,
                upagraha_part=part,
            )
            event_jd_ut = self.timezone_service.to_julian_day_ut(
                birth_data.model_copy(
                    update={
                        "birth_date": event_at.date(),
                        "birth_time": event_at.timetz().replace(tzinfo=None),
                    }
                )
            )
            event_points[name] = self.ephemeris_adapter.calculate_lagna_longitude(
                jd_ut=event_jd_ut,
                latitude=birth_data.latitude,
                longitude=birth_data.longitude,
                profile=profile,
            )
        hora_lagna_longitude = next(
            point.longitude_sidereal for point in points if point.planet == "HL"
        )
        event_points["Varnada"] = compute_varnada_lagna_longitude(
            ascendant_longitude=lagna_longitude,
            hora_lagna_longitude=hora_lagna_longitude,
        )
        for name, longitude in event_points.items():
            points.append(
                build_planet_position(
                    planet_name=name,
                    longitude_sidereal=longitude,
                    speed=1.0,
                    lagna_sign_index=lagna_sign_index,
                )
            )
        return points

    def _adjacent_solar_event(
        self,
        *,
        birth_data: BirthData,
        target_date: int,
        event: str,
    ) -> datetime | None:
        adjacent_birth_data = birth_data.model_copy(
            update={
                "birth_date": date.fromordinal(target_date),
                "birth_time": time(0, 0, 0),
            }
        )
        day_start_jd_ut = self.timezone_service.to_julian_day_ut(adjacent_birth_data)
        sunrise_jd_ut, sunset_jd_ut = self.ephemeris_adapter.calculate_sunrise_sunset(
            jd_ut=day_start_jd_ut,
            latitude=birth_data.latitude,
            longitude=birth_data.longitude,
        )
        event_jd_ut = sunrise_jd_ut if event == "sunrise" else sunset_jd_ut
        return self._local_datetime_or_none(birth_data.timezone, event_jd_ut)

    def _local_datetime_or_none(self, timezone_name: str, jd_ut: float | None) -> datetime | None:
        if jd_ut is None:
            return None
        utc_dt = self.timezone_service.julian_day_ut_to_utc_datetime(jd_ut)
        return self.timezone_service.to_local_timezone(utc_dt, timezone_name)

    def _format_hours(self, hours_value: float) -> str:
        normalized = hours_value % 24.0
        hours = int(normalized)
        minutes_fraction = (normalized - hours) * 60.0
        minutes = int(minutes_fraction)
        seconds = int(round((minutes_fraction - minutes) * 60.0))
        if seconds == 60:
            seconds = 0
            minutes += 1
        if minutes == 60:
            minutes = 0
            hours = (hours + 1) % 24
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
