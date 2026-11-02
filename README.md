# Open Jyotish MCP

吠陀占星（Jyotish）排盘 MCP 服务器。计算内核复用 [OpenJyotish](https://github.com/waka/open-jyotish)（Swiss Ephemeris / `pyswisseph`），无 GUI 依赖，可跑在容器里。

任何 MCP 客户端（Claude Desktop / Claude Code / Cursor / Codex / OpenCode / DeepSeek Harness…）接上后即可让 LLM 直接排盘。

## 能力

| 项 | 内容 |
|---|---|
| 岁差模式 | **47 种**（Lahiri、True Pushya、True Chitra、KP、Raman、Yukteshwar、Fagan-Bradley…）+ 自定义 |
| 分盘 varga | **20 种**（D1/D2/D3/D4/D5/D6/D7/D8/D9/D10/D11/D12/D16/D20/D24/D27/D30/D40/D45/D60） |
| 大运 | Vimshottari 大运 + 全部小运（antardasha） |
| 其他 | Panchanga、Ashtakavarga（含 Samudaya）、Yoga/Dosha、Chara Karaka、六种 Bala、当前行运、Bhava Chart、Moon Chart、Arudha、Argala、Aspects |
| 精度 | 对齐 JHora：`tests/reference` 10 个基准全部通过（行星差 < 0.02°） |

## 工具

| 工具 | 作用 |
|---|---|
| `resolve_place` | 城市名 → 时区 + 经纬度（离线世界城市库，中英文皆可） |
| `compute_chart` | 出生信息 → 完整盘面 JSON（可裁剪重字段） |
| `compute_vargas` | 只算分盘，可指定任意 varga 子集 |
| `compute_dasha` | Vimshottari 大运/小运，给日期可直接定位当前大运 + 小运 |
| `compute_transits` | 行运相对本命盘的落宫、落宫（月亮盘）、与本命的相位 |
| `probe_ayanamsha` | 遍历 47 种岁差 × 真/平节点，按参照值反查对方用的配置 |
| `list_ayanamshas` / `list_vargas` | 配置枚举与含义 |
| `server_info` | 运行状态：实际生效的星历来源、支持数量 |

## 快速开始

### 本地 stdio

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
open-jyotish-mcp
```

MCP 客户端配置见 [`examples/claude_desktop_config.json`](examples/claude_desktop_config.json)。

### 远程 streamable-http

```bash
MCP_TRANSPORT=streamable-http MCP_HOST=0.0.0.0 MCP_PORT=7860 python -m open_jyotish_mcp
# 端点：http://127.0.0.1:7860/mcp
# 健康检查：http://127.0.0.1:7860/healthz
```

客户端填 `https://<你的域名>/mcp`，无需 API key（自建时建议加网关鉴权）。

### Docker

```bash
docker build -t open-jyotish-mcp .
docker run -p 7860:7860 open-jyotish-mcp
```

### 部署到 Hugging Face Spaces（免费，推荐）

1. 新建 Space → SDK 选 **Docker** → 模板 Blank。
2. 把本仓库全部文件推到该 Space 仓库（`README_SPACE.md` 改名成 `README.md`）。
3. Space 自动构建；构建期会编译 `pyswisseph`（约 1–2 分钟）。
4. 端点：`https://<user>-<space>.hf.space/mcp`；健康检查 `…/healthz`。

免费 `cpu-basic` 硬件在 **48 小时无访问后休眠**，有人访问会自动唤醒（冷启动十余秒）。

### 部署到魔搭 ModelScope MCP 广场（国内访问）

在 [modelscope.cn/mcp](https://www.modelscope.cn/mcp) 创建 MCP，选「可托管部署」，填仓库与启动方式（Docker 或 FastMCP 均可），CPU 资源免费。

### 星历文件

`.se1` 已打进 wheel/镜像，装好即用真实 Swiss Ephemeris。若运行在没有包数据的场景（例如手工拷 `src/` 到别处），会回落到内置 Moshier 并在日志里告警——此时 `server_info` 的 `ephemeris` 字段会是 `moshier-fallback`，用它来确认部署是否正常。也可用 `OPEN_JYOTISH_EPHE_PATH` 指定外部星历目录。

## 配置对齐（重要）

不同软件默认岁差不同，配置差一点，整盘行星会整体错位 1° 以上，星宿与宫位全错。若用户给了别的软件（JHora 等）的参照盘：

```jsonc
// probe_ayanamsha
{
  "birth_date": "1992-08-31", "birth_time": "12:00:00",
  "timezone": "Asia/Shanghai", "latitude": 40.58278, "longitude": 110.04611,
  "target_ayanamsha_value": 22.61944,
  "target_lagna": 204.3817
}
```

返回按 `score` 排序的前 5 组配置。本机验证：包头基准锁定 `true_pushya` + `true` node。

## 架构

```
src/open_jyotish/            ← 从 OpenJyotish 抽出的无头计算内核（domain + 星历 + 时区 + 地理）
src/open_jyotish_mcp/        ← MCP 层
├── engine.py                ← 装配、星历路径、地点查表
├── payload.py               ← ChartResult → LLM-ready JSON
└── server.py                ← 9 个 MCP 工具 + stdio / streamable-http / healthz
src/open_jyotish_mcp/ephemeris/  ← Swiss Ephemeris .se1（sepl/semo/seas _18，覆盖 1800–2399，随包分发）
```

内核改动只有一处：`ChartCalculationService.calculate_chart()` 增加可选参数 `transit_as_of`，让 `compute_transits` 能算任意日期的行运（上游仓库未改）。

## 测试

```bash
pytest -q
# 23 passed, 1 skipped
```

- `tests/test_tools.py`：MCP 层，含 JHora 基准断言、参数校验、字段完整性、JSON 可序列化。
- `tests/reference_engine/`：从 OpenJyotish 复制的 JHora 外部基准（10 个样本全过）。

## 上游来源

`src/open_jyotish/` 取自 OpenJyotish 仓库 `03154ac`（initial public release）的 `src/open_jyotish/`，范围限定为无头计算链路：

```
domain/                       rules 与 models，无 Qt 依赖
infrastructure/ephemeris/     Swiss Ephemeris 适配
infrastructure/timezone/      时区 → JD
infrastructure/geo/           离线世界城市库（1.6 MB gz）
application/services/         chart_calculation + reference 比对
```

逐文件与该 commit 比对，除 `chart_calculation_service.py` 增加可选参数 `transit_as_of` 外无改动。GUI（`presentation/`、`app/`、PDF/PNG 导出）未纳入。

## 许可

AGPL-3.0-or-later。内核与 `pyswisseph` 均为 AGPL。公网托管时请在服务说明与页面上提供源码链接以满足 AGPL 第 13 条。

Swiss Ephemeris 星历文件版权归 Astrodienst AG，按 Swiss Ephemeris 的双许可使用（AGPL 或商业许可）。
