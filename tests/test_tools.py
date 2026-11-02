"""MCP 工具层验收：数值正确性、参数校验、字段完整性。"""
from __future__ import annotations

import json

import pytest

from open_jyotish_mcp.server import (
    compute_chart,
    compute_dasha,
    compute_transits,
    compute_vargas,
    list_ayanamshas,
    list_vargas,
    probe_ayanamsha,
    resolve_place,
    server_info,
)

SHANGHAI = {
    "birth_date": "1990-01-01",
    "birth_time": "12:00:00",
    "timezone": "Asia/Shanghai",
    "latitude": 31.2304,
    "longitude": 121.4737,
    "city": "Shanghai",
    "country": "China",
}


@pytest.fixture(scope="module")
def chart():
    return compute_chart(**SHANGHAI, ayanamsha_id="lahiri")


def test_server_info_uses_real_ephemeris():
    info = server_info()
    assert info["ephemeris"].startswith("swisseph:"), info
    assert info["ayanamsha_count"] == 47
    assert info["varga_count"] == 20


def test_compute_chart_matches_jhora_shanghai_baseline(chart):
    # tests/reference_engine/fixtures/shanghai_lahiri.json 的期望值
    assert abs(chart["meta"]["ayanamsha_value"] - 23.717426) < 0.0005
    assert abs(chart["lagna"]["longitude"] - 353.895315) < 0.01

    sun = next(p for p in chart["planets"] if p["planet"] == "Sun")
    assert sun["sign"] == "Sagittarius"
    assert abs(sun["degree_in_sign"] - 16.759515) < 0.01
    assert sun["nakshatra"] == "Purva Ashadha"
    assert sun["pada"] == 2
    assert sun["house"] == 10

    moon = next(p for p in chart["planets"] if p["planet"] == "Moon")
    assert moon["sign"] == "Aquarius"
    assert abs(moon["degree_in_sign"] - 5.068162) < 0.01
    assert moon["nakshatra"] == "Dhanishta"
    assert moon["pada"] == 4
    assert moon["house"] == 12


def test_compute_chart_payload_shape(chart):
    assert set(chart["vargas"].keys()) == {"D1", "D9", "D10"}
    assert len(chart["planets"]) == 9  # 7 行星 + 罗睺 + 计都
    names = {p["planet"] for p in chart["planets"]}
    assert {"Rahu", "Ketu"} <= names
    assert len(chart["vimshottari_dasha"]) == 9
    assert 1 <= len(chart["chara_karakas"]) <= 8
    assert chart["panchanga"]["tithi_name"]
    assert chart["engine"]["ephemeris"].startswith("swisseph:")

    # 输出必须可被 JSON 序列化（MCP 线上传输等价条件）
    json.dumps(chart, ensure_ascii=False)


def test_varga_switches_change_output():
    a = compute_vargas(**SHANGHAI, vargas=["D9"])
    b = compute_vargas(**SHANGHAI, vargas=["D9", "D10", "D60"])
    assert set(a["vargas"]) == {"D9"}
    assert set(b["vargas"]) == {"D9", "D10", "D60"}
    assert a["vargas"]["D9"] == b["vargas"]["D9"]


def test_dasha_locates_active_period():
    result = compute_dasha(**SHANGHAI, at="2026-11-02")
    assert len(result["mahadasha"]) == 9
    active = result["active_at"]
    assert active["as_of"] == "2026-11-02"
    assert active["mahadasha_start"] <= "2026-11-02" <= active["mahadasha_end"]
    assert active["antardasha"] is not None
    assert active["antardasha"]["start"] <= "2026-11-02" <= active["antardasha"]["end"]


def test_dasha_without_date_returns_full_tree():
    result = compute_dasha(**SHANGHAI)
    assert "active_at" not in result
    assert len(result["antardasha"]) == 9


def test_transits_accept_explicit_date():
    result = compute_transits(**SHANGHAI, as_of="2026-11-02")
    assert result["as_of"].startswith("2026-11-02")
    assert len(result["entries"]) >= 9
    entry = result["entries"][0]
    for key in ("planet", "transit_sign", "house_from_lagna", "house_from_moon", "relation_to_natal"):
        assert key in entry


def test_probe_ayanamsha_recovers_known_config():
    """给 JHora 包头基准的 ayanamsha 与上升，应能反查出 true_pushya。"""
    result = probe_ayanamsha(
        birth_date="1992-08-31",
        birth_time="12:00:00",
        timezone="Asia/Shanghai",
        latitude=40.58278,
        longitude=110.04611,
        target_ayanamsha_value=22.61944,
        target_lagna=204.3817,
        node_mode="true",
    )
    assert result["tried"] > 40
    best = result["best"][0]
    assert best["ayanamsha_id"] == "true_pushya"
    assert best["score"] < 0.05


def test_resolve_place_english_and_chinese():
    en = resolve_place("Baotou")
    assert en["count"] >= 1
    assert en["results"][0]["city"] == "Baotou"
    assert en["results"][0]["timezone"] == "Asia/Shanghai"
    zh = resolve_place("上海")
    assert zh["count"] >= 1


def test_invalid_inputs_raise():
    with pytest.raises(ValueError):
        compute_chart(**SHANGHAI, ayanamsha_id="not_a_real_ayanamsha")
    with pytest.raises(ValueError):
        compute_chart(**SHANGHAI, node_mode="maybe")
    with pytest.raises(ValueError):
        compute_vargas(**SHANGHAI, vargas=["D13"])
    with pytest.raises(ValueError):
        compute_chart(**{**SHANGHAI, "timezone": "Nowhere/Land"})


def test_list_catalogs():
    ayan = list_ayanamshas()
    assert ayan["count"] == 47
    assert any(a["id"] == "true_pushya" and a["common"] for a in ayan["ayanamshas"])
    vargas = list_vargas()
    assert vargas["count"] == 20
    assert all(v["meaning"] for v in vargas["vargas"])


def test_outer_planets_flag():
    inner = compute_chart(**SHANGHAI, include_outer_planets=False)
    outer = compute_chart(**SHANGHAI, include_outer_planets=True)
    assert len(outer["planets"]) > len(inner["planets"])


def test_light_mode_drops_heavy_sections():
    light = compute_chart(
        **SHANGHAI,
        include_antardasha=False,
        include_strengths=False,
        include_transits=False,
        include_ashtakavarga=False,
        include_yogas=False,
    )
    for key in ("vimshottari_antardasha", "planet_strengths", "transit_now", "yogas", "doshas"):
        assert key not in light
    assert json.dumps(light, ensure_ascii=False)
