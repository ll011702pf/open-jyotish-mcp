from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import swisseph as swe

from open_jyotish.domain.models.birth_data import BirthData


class TimezoneService:
    def to_julian_day_ut(self, birth_data: BirthData) -> float:
        utc_dt = self.to_utc_datetime(birth_data)
        _, jd_ut = swe.utc_to_jd(
            utc_dt.year,
            utc_dt.month,
            utc_dt.day,
            utc_dt.hour,
            utc_dt.minute,
            utc_dt.second + (utc_dt.microsecond / 1_000_000),
            swe.GREG_CAL,
        )
        return jd_ut

    def to_utc_datetime(self, birth_data: BirthData) -> datetime:
        local_dt = datetime.combine(birth_data.birth_date, birth_data.birth_time)
        try:
            zone = ZoneInfo(birth_data.timezone)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(f"invalid timezone: {birth_data.timezone}") from exc

        zoned_dt = local_dt.replace(tzinfo=zone)
        offset = zoned_dt.utcoffset()
        if offset is None:
            raise ValueError(f"unable to resolve timezone offset: {birth_data.timezone}")

        dst_delta = zoned_dt.dst() or timedelta(0)
        if birth_data.dst_mode == "off":
            offset -= dst_delta
        elif birth_data.dst_mode == "on" and dst_delta == timedelta(0):
            offset += timedelta(hours=1)

        utc_dt = (local_dt - offset).replace(tzinfo=timezone.utc)
        return utc_dt

    def julian_day_ut_to_utc_datetime(self, jd_ut: float) -> datetime:
        year, month, day, hour_fraction = swe.revjul(jd_ut, swe.GREG_CAL)
        hour = int(hour_fraction)
        minute_fraction = (hour_fraction - hour) * 60.0
        minute = int(minute_fraction)
        second_fraction = (minute_fraction - minute) * 60.0
        second = int(second_fraction)
        microsecond = int(round((second_fraction - second) * 1_000_000))
        if microsecond >= 1_000_000:
            second += 1
            microsecond -= 1_000_000
        return datetime(year, month, day, hour, minute, second, microsecond, tzinfo=timezone.utc)

    def to_local_timezone(self, utc_dt: datetime, timezone_name: str) -> datetime:
        try:
            zone = ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(f"invalid timezone: {timezone_name}") from exc
        return utc_dt.astimezone(zone)

    def to_julian_day_ut_from_utc(self, utc_dt: datetime) -> float:
        if utc_dt.tzinfo is None:
            utc_dt = utc_dt.replace(tzinfo=timezone.utc)
        else:
            utc_dt = utc_dt.astimezone(timezone.utc)
        _, jd_ut = swe.utc_to_jd(
            utc_dt.year,
            utc_dt.month,
            utc_dt.day,
            utc_dt.hour,
            utc_dt.minute,
            utc_dt.second + (utc_dt.microsecond / 1_000_000),
            swe.GREG_CAL,
        )
        return jd_ut
