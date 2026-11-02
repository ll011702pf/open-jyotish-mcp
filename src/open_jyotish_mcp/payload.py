"""盘面结果 → LLM-ready JSON。

与 ~/.agents/skills/jyotish-chart/scripts/compute_chart.py 的 build_llm_payload 保持
同一口径（同一套字段名、同样的裁剪范围），并在此基础上补上 MCP 需要的裁剪开关。
"""
from __future__ import annotations

from typing import Any

SIGNS = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)


def sign_of(longitude: float) -> str:
    return SIGNS[int((longitude % 360.0) // 30.0)]


def planet_row(p: Any) -> dict[str, Any]:
    return {
        "planet": p.planet,
        "longitude": round(p.longitude_sidereal, 4),
        "sign": p.sign,
        "degree_in_sign": round(p.degree_in_sign, 4),
        "nakshatra": p.nakshatra,
        "pada": p.pada,
        "house": p.house,
        "dignity": p.dignity,
        "retrograde": bool(p.retrograde),
    }


def dasha_rows(periods) -> list[dict[str, Any]]:
    return [
        {
            "lord": period.lord,
            "start": period.start_at.date().isoformat(),
            "end": period.end_at.date().isoformat(),
            "years": round(period.duration_years, 2),
            "parent": period.parent_lord,
        }
        for period in periods
    ]


def build_llm_payload(
    result,
    *,
    vargas: tuple[str, ...] = ("D1", "D9", "D10"),
    include_antardasha: bool = True,
    include_ashtakavarga: bool = True,
    include_strengths: bool = True,
    include_transits: bool = True,
    include_yogas: bool = True,
) -> dict[str, Any]:
    """把 ChartResult 裁剪成可读性优先的 JSON。"""
    payload: dict[str, Any] = {
        "meta": {
            "title": result.birth_data.title,
            "subject_name": result.birth_data.subject_name,
            "birth": {
                "date": result.birth_data.birth_date.isoformat(),
                "time": result.birth_data.birth_time.isoformat(),
                "timezone": result.birth_data.timezone,
                "city": result.birth_data.city,
                "country": result.birth_data.country,
                "latitude": result.birth_data.latitude,
                "longitude": result.birth_data.longitude,
            },
            "ayanamsha": result.profile.ayanamsha_id.value,
            "ayanamsha_value": round(result.ayanamsha_value, 5),
            "house_system": result.profile.house_system,
            "node_mode": result.profile.node_mode,
            "jd_ut": round(result.jd_ut, 6),
            "computed_at": result.computed_at.isoformat(timespec="seconds"),
        },
        "lagna": {
            "longitude": round(result.lagna_longitude, 4),
            "sign": sign_of(result.lagna_longitude),
            "degree_in_sign": round(result.lagna_longitude % 30.0, 4),
        },
        "planets": [planet_row(p) for p in result.planets],
        "houses": [round(cusp, 4) for cusp in result.houses],
        "vimshottari_dasha": dasha_rows(result.vimshottari_dasha),
        "chara_karakas": [
            {"role": k.role, "planet": k.planet, "meaning": k.meaning}
            for k in result.chara_karakas
        ],
        "panchanga": result.panchanga.model_dump(mode="json") if result.panchanga else None,
    }

    if vargas:
        payload["vargas"] = {
            name: {
                "lagna_sign": sign_of(v.lagna_longitude),
                "lagna_degree_in_sign": round(v.lagna_longitude % 30.0, 4),
                "planet_signs": {p.planet: p.sign for p in v.planets},
                "planet_degrees": {
                    p.planet: round(p.degree_in_sign, 4) for p in v.planets
                },
            }
            for name, v in result.vargas.items()
            if name in vargas
        }

    if include_antardasha:
        payload["vimshottari_antardasha"] = {
            lord: dasha_rows(periods)
            for lord, periods in result.vimshottari_antardasha.items()
        }

    if include_yogas:
        payload["yogas"] = [
            {"name": y.name, "key": y.key, "category": y.category, "description": y.description}
            for y in result.yogas
        ]
        payload["doshas"] = [
            {"name": d.name, "severity": d.severity, "description": d.description}
            for d in result.doshas
        ]

    if include_strengths:
        payload["planet_strengths"] = [
            {
                "planet": s.planet,
                **{
                    key: round(value, 2)
                    for key, value in s.model_dump().items()
                    if key != "planet" and isinstance(value, (int, float))
                },
            }
            for s in result.planet_strengths
        ]

    if include_transits and result.transit_snapshot:
        payload["transit_now"] = {
            "as_of": result.transit_snapshot.as_of_local.isoformat(timespec="hours"),
            "entries": [
                {
                    "planet": e.planet,
                    "transit_sign": e.transit_sign,
                    "house_from_lagna": e.house_from_lagna,
                    "house_from_moon": e.house_from_moon,
                }
                for e in result.transit_snapshot.entries
            ],
        }

    if include_ashtakavarga and result.ashtakavarga is not None and result.ashtakavarga.samudaya:
        payload["ashtakavarga_samudaya"] = {
            SIGNS[i]: int(v) for i, v in enumerate(result.ashtakavarga.samudaya)
        }

    return payload
