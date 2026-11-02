"""Open Jyotish MCP 服务端。

把 OpenJyotish 的无头计算内核（Swiss Ephemeris + 47 种岁差 + 20 种 varga +
Vimshottari 大运）包装成 MCP 工具，任何 MCP 客户端都能直接排盘。
"""
from __future__ import annotations

import argparse
import os
from datetime import date, datetime
from datetime import time as dt_time
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from mcp.server.mcpserver import MCPServer

from open_jyotish.domain.rules.vargas import STANDARD_VARGAS
from open_jyotish_mcp.engine import JyotishEngine, ayanamsha_catalog, ephemeris_mode
from open_jyotish_mcp.payload import build_llm_payload, sign_of

SERVER_INSTRUCTIONS = """\
Open Jyotish —— 印度占星（吠陀）排盘服务器。

先 resolve_place 拿时区与经纬度（不要猜坐标），再 compute_chart 出盘。
默认配置 true_pushya + true node，已对 JHora 逐行星验证（差 <30 角秒）。
若用户给了别的软件（JHora/其他）的参照盘，先用 probe_ayanamsha 对齐配置，
否则整盘行星会整体错位 1° 以上，星宿与宫位全错。
出生时间未知时用 12:00，并在解读时声明上升/宫位相关项不可用。
"""

mcp = MCPServer(
    name="open-jyotish",
    title="Open Jyotish (Vedic Astrology)",
    version="0.1.0",
    instructions=SERVER_INSTRUCTIONS,
)

_engine = JyotishEngine()


# ---------------------------------------------------------------------------
# 地点
# -------------------------------------------------------------------------_
@mcp.tool()
def resolve_place(query: str, limit: int = 8) -> dict[str, Any]:
    """查城市 → 时区 + 经纬度（离线世界城市库，不联网）。

    Args:
        query: 城市名，中英文皆可（如 "Baotou"、"包头"、"New York"）；留空则返回人口最多的城市。
        limit: 返回条数上限，1-20。
    """
    limit = max(1, min(20, int(limit)))
    results = _engine.resolve_place(query, limit=limit)
    return {"query": query, "count": len(results), "results": results}


# ---------------------------------------------------------------------------
# 排盘
# ---------------------------------------------------------------------------
@mcp.tool()
def compute_chart(
    birth_date: str,
    timezone: str,
    latitude: float,
    longitude: float,
    birth_time: str = "12:00:00",
    city: str = "",
    country: str = "",
    title: str = "chart",
    subject_name: str = "",
    ayanamsha_id: str = "true_pushya",
    node_mode: str = "true",
    house_system: str = "whole_sign",
    dst_mode: str = "auto",
    include_outer_planets: bool = False,
    vargas: list[str] | None = None,
    include_antardasha: bool = True,
    include_yogas: bool = True,
    include_strengths: bool = True,
    include_transits: bool = True,
    include_ashtakavarga: bool = True,
) -> dict[str, Any]:
    """出生信息 → 完整盘面 JSON（行星/宫位/星宿、varga、大运、yoga/dosha、panchanga、行运）。

    Args:
        birth_date: 公历日期 YYYY-MM-DD。
        timezone: IANA 时区，如 Asia/Shanghai。
        latitude: 纬度（北正南负）。
        longitude: 经度（东正西负）。
        birth_time: 本地出生时间 HH:MM 或 HH:MM:SS，未知时留默认 12:00:00。
        city: 城市名，仅用于标注。
        country: 国家名，仅用于标注。
        title: 盘面标题。
        subject_name: 命主标识，留空则等于 title。
        ayanamsha_id: 岁差模式，见 list_ayanamshas；默认 true_pushya。
        node_mode: 罗睺模式 "true"（真节点）或 "mean"（平节点）。
        house_system: 宫位制，whole_sign / equal / placidus 等。
        dst_mode: 夏令时处理 auto / on / off。
        include_outer_planets: 是否含天王星/海王星/冥王星。
        vargas: 要输出的分盘，默认 ["D1","D9","D10"]；可用 list_vargas 查全部。
        include_antardasha: 是否输出全部小运（数据量大，默认开）。
        include_yogas: 是否输出 yoga / dosha。
        include_strengths: 是否输出行星力量六种 bala。
        include_transits: 是否输出当前行运相对本命盘的位置。
        include_ashtakavarga: 是否输出 ashtakavarga 总和。
    """
    if node_mode not in ("true", "mean"):
        raise ValueError("node_mode must be 'true' or 'mean'")
    varga_list = tuple(vargas) if vargas else ("D1", "D9", "D10")
    unknown = [v for v in varga_list if v not in STANDARD_VARGAS]
    if unknown:
        raise ValueError(f"unknown vargas: {unknown}; known: {list(STANDARD_VARGAS)}")

    result = _engine.calculate(
        birth_date=birth_date,
        birth_time=birth_time,
        timezone=timezone,
        latitude=latitude,
        longitude=longitude,
        title=title,
        subject_name=subject_name or title,
        city=city,
        country=country,
        ayanamsha_id=ayanamsha_id,
        house_system=house_system,
        node_mode=node_mode,
        dst_mode=dst_mode,
        include_outer_planets=include_outer_planets,
        enabled_vargas=list(varga_list),
    )
    payload = build_llm_payload(
        result,
        vargas=varga_list,
        include_antardasha=include_antardasha,
        include_ashtakavarga=include_ashtakavarga,
        include_strengths=include_strengths,
        include_transits=include_transits,
        include_yogas=include_yogas,
    )
    payload["engine"] = {"ephemeris": ephemeris_mode(), "server": "open-jyotish-mcp"}
    return payload


# ---------------------------------------------------------------------------
# 单项查询：比整盘轻，适合追问
# ---------------------------------------------------------------------------
def _base_result(
    birth_date: str,
    timezone: str,
    latitude: float,
    longitude: float,
    birth_time: str,
    ayanamsha_id: str,
    node_mode: str,
    house_system: str,
    dst_mode: str,
):
    return _engine.calculate(
        birth_date=birth_date,
        birth_time=birth_time,
        timezone=timezone,
        latitude=latitude,
        longitude=longitude,
        ayanamsha_id=ayanamsha_id,
        node_mode=node_mode,
        house_system=house_system,
        dst_mode=dst_mode,
        enabled_vargas=["D1"],
    )


@mcp.tool()
def compute_vargas(
    birth_date: str,
    timezone: str,
    latitude: float,
    longitude: float,
    birth_time: str = "12:00:00",
    vargas: list[str] | None = None,
    ayanamsha_id: str = "true_pushya",
    node_mode: str = "true",
    house_system: str = "whole_sign",
    dst_mode: str = "auto",
    city: str = "",
    country: str = "",
) -> dict[str, Any]:
    """只算分盘（varga）：每个 varga 的上升与全部行星落座。

    Args:
        birth_date: 公历日期 YYYY-MM-DD。
        timezone: IANA 时区。
        latitude: 纬度。
        longitude: 经度。
        birth_time: 本地时间 HH:MM[:SS]。
        vargas: 要算的分盘列表，默认全部 20 种；用 list_vargas 查可用值。
        ayanamsha_id: 岁差模式。
        node_mode: "true" 或 "mean"。
        house_system: 宫位制。
        dst_mode: auto / on / off。
    """
    requested = tuple(vargas) if vargas else tuple(STANDARD_VARGAS)
    unknown = [v for v in requested if v not in STANDARD_VARGAS]
    if unknown:
        raise ValueError(f"unknown vargas: {unknown}; known: {list(STANDARD_VARGAS)}")
    result = _engine.calculate(
        birth_date=birth_date,
        birth_time=birth_time,
        timezone=timezone,
        latitude=latitude,
        longitude=longitude,
        ayanamsha_id=ayanamsha_id,
        node_mode=node_mode,
        house_system=house_system,
        dst_mode=dst_mode,
        city=city,
        country=country,
        enabled_vargas=list(requested),
    )
    return {
        "meta": {
            "ayanamsha": result.profile.ayanamsha_id.value,
            "ayanamsha_value": round(result.ayanamsha_value, 5),
            "node_mode": result.profile.node_mode,
        },
        "lagna": {
            "longitude": round(result.lagna_longitude, 4),
            "sign": sign_of(result.lagna_longitude),
        },
        "vargas": {
            name: {
                "lagna_sign": sign_of(v.lagna_longitude),
                "lagna_degree_in_sign": round(v.lagna_longitude % 30.0, 4),
                "planet_signs": {p.planet: p.sign for p in v.planets},
            }
            for name, v in result.vargas.items()
            if name in requested
        },
    }


@mcp.tool()
def compute_dasha(
    birth_date: str,
    timezone: str,
    latitude: float,
    longitude: float,
    birth_time: str = "12:00:00",
    ayanamsha_id: str = "true_pushya",
    node_mode: str = "true",
    at: str = "",
    city: str = "",
    country: str = "",
) -> dict[str, Any]:
    """Vimshottari 大运 / 小运；给了 at 就定位到那一天。

    Args:
        birth_date: 公历日期 YYYY-MM-DD。
        timezone: IANA 时区。
        latitude: 纬度。
        longitude: 经度。
        birth_time: 本地时间 HH:MM[:SS]。
        ayanamsha_id: 岁差模式。
        node_mode: "true" 或 "mean"。
        at: 可选，查询日期 YYYY-MM-DD；留空则返回全部 9 个大运及其小运。
    """
    result = _base_result(
        birth_date, timezone, latitude, longitude,
        birth_time, ayanamsha_id, node_mode, "whole_sign", "auto",
    )
    mahadasha = [
        {
            "lord": p.lord,
            "start": p.start_at.date().isoformat(),
            "end": p.end_at.date().isoformat(),
            "years": round(p.duration_years, 3),
        }
        for p in result.vimshottari_dasha
    ]
    payload: dict[str, Any] = {"mahadasha": mahadasha}

    active = None
    if at:
        target = date.fromisoformat(at)
        for period in result.vimshottari_dasha:
            if period.start_at.date() <= target <= period.end_at.date():
                subs = result.vimshottari_antardasha.get(period.lord, [])
                active = {
                    "as_of": at,
                    "mahadasha": period.lord,
                    "mahadasha_start": period.start_at.date().isoformat(),
                    "mahadasha_end": period.end_at.date().isoformat(),
                    "antardasha": next(
                        (
                            {
                                "lord": s.lord,
                                "start": s.start_at.date().isoformat(),
                                "end": s.end_at.date().isoformat(),
                            }
                            for s in subs
                            if s.start_at.date() <= target <= s.end_at.date()
                        ),
                        None,
                    ),
                }
                break
    if active is not None:
        payload["active_at"] = active
    else:
        payload["antardasha"] = {
            lord: [
                {"lord": p.lord, "start": p.start_at.date().isoformat(), "end": p.end_at.date().isoformat()}
                for p in periods
            ]
            for lord, periods in result.vimshottari_antardasha.items()
        }
    return payload


@mcp.tool()
def compute_transits(
    birth_date: str,
    timezone: str,
    latitude: float,
    longitude: float,
    birth_time: str = "12:00:00",
    ayanamsha_id: str = "true_pushya",
    node_mode: str = "true",
    as_of: str = "",
    city: str = "",
    country: str = "",
) -> dict[str, Any]:
    """当前（或指定日期）行运相对本命盘的落宫与相位关系。

    Args:
        birth_date: 本命公历日期 YYYY-MM-DD。
        timezone: IANA 时区（也是行运日期的解释时区）。
        latitude: 纬度。
        longitude: 经度。
        birth_time: 本地出生时间 HH:MM[:SS]。
        ayanamsha_id: 岁差模式。
        node_mode: "true" 或 "mean"。
        as_of: 可选行运日期 YYYY-MM-DD，留空用当前时刻。
    """
    transit_as_of = None
    if as_of:
        try:
            zone = ZoneInfo(timezone)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(f"invalid timezone: {timezone}") from exc
        transit_as_of = datetime.combine(
            date.fromisoformat(as_of), dt_time(12, 0)
        ).replace(tzinfo=zone)

    result = _engine.calculate(
        birth_date=birth_date, birth_time=birth_time, timezone=timezone,
        latitude=latitude, longitude=longitude,
        ayanamsha_id=ayanamsha_id, node_mode=node_mode,
        house_system="whole_sign", dst_mode="auto",
        city=city, country=country,
        enabled_vargas=["D1"], transit_as_of=transit_as_of,
    )
    snapshot = result.transit_snapshot
    entries = [
        {
            "planet": e.planet,
            "transit_sign": e.transit_sign,
            "transit_degree": round(e.transit_degree, 4),
            "house_from_lagna": e.house_from_lagna,
            "house_from_moon": e.house_from_moon,
            "natal_sign": e.natal_sign,
            "relation_to_natal": e.relation_to_natal,
            "orb_degrees": round(e.orb_degrees, 3) if e.orb_degrees is not None else None,
            "retrograde": e.retrograde,
        }
        for e in snapshot.entries
    ]
    payload: dict[str, Any] = {
        "as_of": snapshot.as_of_local.isoformat(timespec="minutes"),
        "timezone": snapshot.timezone,
        "entries": entries,
    }
    return payload


# ---------------------------------------------------------------------------
# 配置对齐
# ---------------------------------------------------------------------------
@mcp.tool()
def probe_ayanamsha(
    birth_date: str,
    timezone: str,
    latitude: float,
    longitude: float,
    birth_time: str = "12:00:00",
    target_ayanamsha_value: float | None = None,
    target_lagna: float | None = None,
    node_mode: str = "",
    city: str = "",
    country: str = "",
) -> dict[str, Any]:
    """遍历全部 47 种岁差（× 真/平节点），按给定的参照值反查对方用的配置。

    用于对齐 JHora 等软件的基准盘：配置差一点，整盘行星就会错位 1° 以上。

    Args:
        birth_date: 公历日期 YYYY-MM-DD。
        timezone: IANA 时区。
        latitude: 纬度。
        longitude: 经度。
        birth_time: 本地时间 HH:MM[:SS]。
        target_ayanamsha_value: 参照盘的 ayanamsha 度数（如 22.61944），可省略。
        target_lagna: 参照盘的上升绝对经度（如 204.3817），可省略。
        node_mode: 限定 "true"/"mean"，留空两种都试。
    """
    from open_jyotish.domain.enums.ayanamsha import AYANAMSHA_OPTIONS

    modes = [node_mode] if node_mode else ["true", "mean"]
    rows: list[dict[str, Any]] = []
    for ayan in AYANAMSHA_OPTIONS:
        for mode in modes:
            try:
                result = _engine.calculate(
                    birth_date=birth_date,
                    birth_time=birth_time,
                    timezone=timezone,
                    latitude=latitude,
                    longitude=longitude,
                    ayanamsha_id=ayan.value,
                    node_mode=mode,
                    city=city,
                    country=country,
                    enabled_vargas=["D1"],
                )
            except Exception as exc:  # noqa: BLE001
                rows.append(
                    {"ayanamsha_id": ayan.value, "node_mode": mode, "error": str(exc)[:120]}
                )
                continue
            row: dict[str, Any] = {
                "ayanamsha_id": ayan.value,
                "node_mode": mode,
                "ayanamsha_value": round(result.ayanamsha_value, 6),
                "lagna_longitude": round(result.lagna_longitude, 6),
                "lagna_sign": sign_of(result.lagna_longitude),
            }
            score = 0.0
            if target_ayanamsha_value is not None:
                row["ayanamsha_diff"] = round(
                    abs(result.ayanamsha_value - target_ayanamsha_value), 6
                )
                score += row["ayanamsha_diff"]
            if target_lagna is not None:
                diff = abs(result.lagna_longitude - target_lagna) % 360.0
                diff = min(diff, 360.0 - diff)
                row["lagna_diff"] = round(diff, 6)
                score += diff
            row["score"] = (
                round(score, 6)
                if (target_ayanamsha_value is not None or target_lagna is not None)
                else None
            )
            rows.append(row)

    ranked = sorted(
        (r for r in rows if r.get("score") is not None),
        key=lambda r: r["score"],
    )
    return {
        "tried": len(rows),
        "targets": {"ayanamsha_value": target_ayanamsha_value, "lagna": target_lagna},
        "best": ranked[:5],
        "all": rows,
    }


# ---------------------------------------------------------------------------
# 元数据
# ---------------------------------------------------------------------------
@mcp.tool()
def list_ayanamshas() -> dict[str, Any]:
    """列出全部可用岁差模式，标注常用的几个。"""
    items = ayanamsha_catalog()
    return {"count": len(items), "ayanamshas": items}


@mcp.tool()
def list_vargas() -> dict[str, Any]:
    """列出全部可用分盘（varga）及其含义。"""
    meaning = {
        "D1": "Rashi，本命盘（身体与整体人生）",
        "D2": "Hora，财富",
        "D3": "Drekkana，兄弟姐妹",
        "D4": "Chaturthamsha，不动产与家",
        "D5": "Panchamsha，福德/子女",
        "D6": "Shashthamsha，健康与疾病",
        "D7": "Saptamsha，子女",
        "D8": "Ashtamsha，意外与寿命",
        "D9": "Navamsha，婚姻与后半生（最重要）",
        "D10": "Dashamsha，事业",
        "D11": "Rudramsha，增益与损失",
        "D12": "Dwadashamsha，父母",
        "D16": "Shodashamsha，交通工具与安逸",
        "D20": "Vimshamsha，灵性修行",
        "D24": "Chaturvimshamsha，学习与教育",
        "D27": "Saptavimshamsha，天赋与强弱",
        "D30": "Trimshamsha，灾厄",
        "D40": "Khavedamsha，母系遗产",
        "D45": "Akshavedamsha，父系遗产",
        "D60": "Shashtiamsha，前世业力（最细）",
    }
    return {
        "count": len(STANDARD_VARGAS),
        "vargas": [
            {"id": v, "meaning": meaning.get(v, "")} for v in STANDARD_VARGAS
        ],
    }


@mcp.tool()
def server_info() -> dict[str, Any]:
    """服务的运行状态：星历来源、时区库、支持的岁差/varga 数量。"""
    return {
        "name": "open-jyotish-mcp",
        "version": "0.1.0",
        "ephemeris": ephemeris_mode(),
        "ayanamsha_count": len(ayanamsha_catalog()),
        "varga_count": len(STANDARD_VARGAS),
        "engine": "OpenJyotish (Swiss Ephemeris via pyswisseph)",
    }


# ---------------------------------------------------------------------------
# 传输层
# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="open-jyotish-mcp")
    parser.add_argument(
        "--transport",
        choices=("stdio", "streamable-http", "sse"),
        default=os.environ.get("MCP_TRANSPORT", "stdio"),
    )
    parser.add_argument("--host", default=os.environ.get("MCP_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("MCP_PORT", "8000")))
    parser.add_argument("--path", default=os.environ.get("MCP_PATH", "/mcp"))
    args = parser.parse_args(argv)

    if args.transport == "stdio":
        mcp.run("stdio")
        return
    if args.transport == "sse":
        mcp.run("sse", host=args.host, port=args.port)
        return

    import uvicorn

    uvicorn.run(
        build_asgi_app(path=args.path),
        host=args.host,
        port=args.port,
        log_level=os.environ.get("MCP_LOG_LEVEL", "info").lower(),
    )


def build_asgi_app(*, path: str = "/mcp"):
    """MCP streamable-http + /healthz（平台健康检查与冷启动探活用）。"""
    from starlette.applications import Starlette
    from starlette.requests import Request
    from starlette.responses import JSONResponse
    from starlette.routing import Mount, Route

    inner = mcp.streamable_http_app(
        streamable_http_path=path,
        stateless_http=os.environ.get("MCP_STATELESS", "1") == "1",
        host=os.environ.get("MCP_HOST", "0.0.0.0"),
        transport_security=_transport_security(),
    )

    async def healthz(_: Request) -> JSONResponse:
        return JSONResponse(
            {
                "status": "ok",
                "server": "open-jyotish-mcp",
                "ephemeris": ephemeris_mode(),
                "tools": 9,
            }
        )

    return Starlette(
        routes=[Route("/healthz", healthz), Mount("/", app=inner)],
        lifespan=inner.router.lifespan_context,
    )


def _transport_security():
    """公网部署时允许任意 Host（HF Spaces / 魔搭 的域名不固定）。"""
    try:
        from mcp.server.transport_security import TransportSecuritySettings
    except ImportError:  # pragma: no cover - 老版本 SDK 没有这个模块
        return None
    if os.environ.get("MCP_ALLOW_ANY_HOST", "1") != "1":
        return None
    return TransportSecuritySettings(
        allowed_hosts=["*"],
        allowed_origins=["*"],
        enable_dns_rebinding_protection=False,
    )


if __name__ == "__main__":  # pragma: no cover
    main()
