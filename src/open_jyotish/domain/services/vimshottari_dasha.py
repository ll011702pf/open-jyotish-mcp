from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from open_jyotish.domain.models.chart_result import DashaPeriod
from open_jyotish.domain.models.chart_result import PlanetPosition


VIMSHOTTARI_SEQUENCE = (
    ("Ketu", 7),
    ("Venus", 20),
    ("Sun", 6),
    ("Moon", 10),
    ("Mars", 7),
    ("Rahu", 18),
    ("Jupiter", 16),
    ("Saturn", 19),
    ("Mercury", 17),
)

NAKSHATRA_SPAN = 360.0 / 27.0
YEAR_DAYS = 365.2425
TOTAL_VIMSHOTTARI_YEARS = sum(years for _, years in VIMSHOTTARI_SEQUENCE)


@dataclass(slots=True)
class VimshottariDashaService:
    def build_mahadasha_periods(
        self,
        *,
        birth_utc: datetime,
        moon: PlanetPosition,
    ) -> list[DashaPeriod]:
        if birth_utc.tzinfo is None:
            birth_utc = birth_utc.replace(tzinfo=timezone.utc)

        nakshatra_index = int(moon.longitude_sidereal // NAKSHATRA_SPAN)
        traversed_in_nakshatra = moon.longitude_sidereal - (nakshatra_index * NAKSHATRA_SPAN)
        traversed_fraction = traversed_in_nakshatra / NAKSHATRA_SPAN

        current_index = nakshatra_index % len(VIMSHOTTARI_SEQUENCE)
        periods: list[DashaPeriod] = []
        current_start = birth_utc

        for step in range(len(VIMSHOTTARI_SEQUENCE)):
            lord, years = VIMSHOTTARI_SEQUENCE[(current_index + step) % len(VIMSHOTTARI_SEQUENCE)]
            active_years = years
            if step == 0:
                active_years = years * (1.0 - traversed_fraction)
            current_end = current_start + timedelta(days=active_years * YEAR_DAYS)
            periods.append(
                DashaPeriod(
                    level="mahadasha",
                    lord=lord,
                    start_at=current_start,
                    end_at=current_end,
                    duration_years=active_years,
                )
            )
            current_start = current_end

        return periods

    def build_antardasha_periods(
        self,
        *,
        mahadasha_periods: list[DashaPeriod],
    ) -> dict[str, list[DashaPeriod]]:
        period_map: dict[str, list[DashaPeriod]] = {}

        for mahadasha in mahadasha_periods:
            start_index = next(
                index for index, (lord, _) in enumerate(VIMSHOTTARI_SEQUENCE) if lord == mahadasha.lord
            )
            antardashas: list[DashaPeriod] = []
            current_start = mahadasha.start_at

            for offset in range(len(VIMSHOTTARI_SEQUENCE)):
                sub_lord, sub_years = VIMSHOTTARI_SEQUENCE[(start_index + offset) % len(VIMSHOTTARI_SEQUENCE)]
                active_years = mahadasha.duration_years * (sub_years / TOTAL_VIMSHOTTARI_YEARS)
                current_end = current_start + timedelta(days=active_years * YEAR_DAYS)
                antardashas.append(
                    DashaPeriod(
                        level="antardasha",
                        lord=sub_lord,
                        start_at=current_start,
                        end_at=current_end,
                        duration_years=active_years,
                        parent_lord=mahadasha.lord,
                    )
                )
                current_start = current_end

            if antardashas:
                antardashas[-1].end_at = mahadasha.end_at
            period_map[mahadasha.lord] = antardashas

        return period_map

    def find_active_period(
        self,
        *,
        periods: list[DashaPeriod],
        at: datetime,
    ) -> DashaPeriod | None:
        if at.tzinfo is None:
            at = at.replace(tzinfo=timezone.utc)

        for period in periods:
            if period.start_at <= at < period.end_at:
                return period

        if periods and at >= periods[-1].end_at:
            return periods[-1]
        return None
