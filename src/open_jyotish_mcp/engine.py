"""计算引擎装配：星历路径、时区、地点查表、排盘入口。"""
from __future__ import annotations

import logging
import os
import threading
from datetime import date, datetime, time
from pathlib import Path
from typing import Any

import swisseph as swe

from open_jyotish.application.services.chart_calculation_service import (
    ChartCalculationService,
)
from open_jyotish.domain.enums.ayanamsha import AyanamshaId
from open_jyotish.domain.models.birth_data import BirthData
from open_jyotish.domain.models.calculation_profile import CalculationProfile
from open_jyotish.domain.rules.vargas import DEFAULT_ENABLED_VARGAS
from open_jyotish.infrastructure.ephemeris.swiss_ephemeris_adapter import (
    SwissEphemerisAdapter,
)
from open_jyotish.infrastructure.geo.place_lookup_service import PlaceLookupService
from open_jyotish.infrastructure.timezone.timezone_service import TimezoneService

_EPHEMERIS_ENV = "OPEN_JYOTISH_EPHE_PATH"

_lock = threading.Lock()
_initialised = False
_ephemeris_mode = "moshier"


def ephemeris_dir() -> Path | None:
    """星历目录：环境变量优先，其次仓库内 ephemeris/，最后包内 ephemeris/。"""
    candidates: list[Path] = []
    env = os.environ.get(_EPHEMERIS_ENV)
    if env:
        candidates.append(Path(env).expanduser())
    here = Path(__file__).resolve()
    candidates.append(here.parent / "ephemeris")               # 包内（wheel 安装）
    candidates.append(here.parent.parent.parent / "ephemeris")  # 源码仓库根
    for candidate in candidates:
        if candidate.is_dir() and any(candidate.glob("*.se1")):
            return candidate
    return None


def initialise() -> str:
    """进程内一次性装配 swisseph 全局状态；返回实际使用的星历模式。"""
    global _initialised, _ephemeris_mode
    with _lock:
        if _initialised:
            return _ephemeris_mode
        path = ephemeris_dir()
        if path is not None:
            swe.set_ephe_path(str(path))
            _ephemeris_mode = f"swisseph:{path.name}"
        else:
            # 没有 .se1 时 swisseph 会静默回落到 Moshier：能算，但不是 JPL 精度。
            _ephemeris_mode = "moshier-fallback"
            logging.getLogger("open_jyotish_mcp").warning(
                "no Swiss Ephemeris .se1 files found; falling back to the built-in "
                "Moshier ephemeris (lower precision, differs from JPL at the arcsecond "
                "level). Set %s to a directory containing sepl_18.se1 / semo_18.se1 / "
                "seas_18.se1 to fix this.",
                _EPHEMERIS_ENV,
            )
        _initialised = True
        return _ephemeris_mode


def ephemeris_mode() -> str:
    initialise()
    return _ephemeris_mode


def zen_mode() -> str:
    """swisseph 在找不到 .se1 时会静默回落到 Moshier，这里主动探一次。"""
    return ephemeris_mode()


class JyotishEngine:
    """无状态排盘引擎；线程安全（每次调用独立构造 service）。"""

    def __init__(self) -> None:
        initialise()
        self._places = PlaceLookupService()

    # -- 地点 --------------------------------------------------------------
    def resolve_place(self, query: str, *, limit: int = 8) -> list[dict[str, Any]]:
        records = self._places.search_places(query, limit=limit)
        return [
            {
                "city": r.city,
                "country": r.country,
                "timezone": r.timezone,
                "latitude": r.latitude,
                "longitude": r.longitude,
                "population": r.population,
                "label": r.label,
            }
            for r in records
        ]

    # -- 盘面 --------------------------------------------------------------
    def calculate(
        self,
        *,
        birth_date: str,
        birth_time: str = "12:00:00",
        timezone: str,
        latitude: float,
        longitude: float,
        title: str = "chart",
        subject_name: str | None = None,
        city: str | None = None,
        country: str | None = None,
        ayanamsha_id: str = "true_pushya",
        house_system: str = "whole_sign",
        node_mode: str = "true",
        dst_mode: str = "auto",
        include_outer_planets: bool = False,
        enabled_vargas: list[str] | None = None,
        transit_as_of: datetime | None = None,
    ):
        birth = BirthData(
            title=title,
            subject_name=subject_name or title,
            birth_date=date.fromisoformat(birth_date),
            birth_time=_parse_time(birth_time),
            timezone=timezone,
            dst_mode=dst_mode,
            latitude=float(latitude),
            longitude=float(longitude),
            country=country,
            city=city or _fallback_city(latitude, longitude),
        )
        profile = CalculationProfile(
            ayanamsha_id=AyanamshaId(ayanamsha_id),
            house_system=house_system,
            node_mode=node_mode,
            include_outer_planets=include_outer_planets,
            enabled_vargas=_with_d1(enabled_vargas),
        )
        service = ChartCalculationService(
            timezone_service=TimezoneService(),
            ephemeris_adapter=SwissEphemerisAdapter(),
        )
        kwargs = {"transit_as_of": transit_as_of} if transit_as_of is not None else {}
        return service.calculate_chart(birth, profile, **kwargs)


def _fallback_city(latitude: float, longitude: float) -> str:
    """BirthData 要求 city 非空；没给就用坐标兜底。"""
    return f"{float(latitude):.4f},{float(longitude):.4f}"


def _with_d1(vargas: list[str] | None) -> list[str]:
    """引擎要求 D1 始终启用（其余 varga 都从 D1 推导）。"""
    wanted = [v.strip().upper() for v in (vargas or []) if v and v.strip()]
    if "D1" not in wanted:
        wanted.insert(0, "D1")
    return wanted or list(DEFAULT_ENABLED_VARGAS)


def _parse_time(value: str) -> time:
    parts = (value or "12:00:00").strip().split(":")
    hour = int(parts[0])
    minute = int(parts[1]) if len(parts) > 1 else 0
    second = int(float(parts[2])) if len(parts) > 2 else 0
    return time(hour, minute, second)


def ayanamsha_catalog() -> list[dict[str, Any]]:
    """枚举全部岁差模式，附带说明哪些是常用的。"""
    common = {
        "lahiri": "Lahiri / Chitrapaksha，印度官方标准，最常用",
        "true_pushya": "True Pushya（本机已对 JHora 逐行星验证）",
        "true_citra": "True Chitra，JHora 默认之一",
        "true_revati": "True Revati",
        "krishnamurti": "KP (Krishnamurti) 恒星黄道",
        "raman": "B.V. Raman",
        "yukteshwar": "Sri Yukteshwar",
        "fagan_bradley": "Fagan-Bradley，西方恒星占星常用",
        "ss_citra": "Surya Siddhanta Citra",
        "true_mula": "True Mula",
    }
    return [
        {"id": member.value, "common": member.value in common, "note": common.get(member.value, "")}
        for member in AyanamshaId
        if member != AyanamshaId.CUSTOM
    ]
