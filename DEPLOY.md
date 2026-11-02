# 部署清单

## 0. 部署前自检（本地）

```bash
.venv/bin/python -m pytest -q                    # 23 passed, 1 skipped
.venv/bin/python -c "from open_jyotish_mcp.server import server_info; print(server_info())"
# 必须看到 'ephemeris': 'swisseph:...'，不能是 moshier-fallback
```

## 1. Hugging Face Spaces（免费公网，首选）

1. 建 Space：<https://huggingface.co/new-space> → **SDK: Docker** → Blank 模板
2. 推代码（把 `README_SPACE.md` 覆盖成 Space 的 `README.md`）：

```bash
git init && git add -A && git commit -m "open-jyotish-mcp 0.1.0"
git remote add space https://huggingface.co/spaces/<user>/<space>
git push space main
```

3. 构建约 2–4 分钟（含 `pyswisseph` C 扩展编译）
4. 验收：

```bash
curl https://<user>-<space>.hf.space/healthz
# {"status":"ok","ephemeris":"swisseph:...","tools":9}
```

客户端填 `https://<user>-<space>.hf.space/mcp`。

> 免费 `cpu-basic`：**48 小时无访问后休眠**，下次访问自动唤醒（冷启动十余秒）。

## 2. 魔搭 ModelScope（国内直连）

1. 打开 <https://www.modelscope.cn/mcp> → 创建 MCP
2. 托管方式选「**可托管部署**」（用魔搭免费资源跑，CPU 免费）
3. 填仓库地址与启动方式，提交审核
4. 审核通过后获得 `https://mcp.modelscope.cn/...` 形式的托管地址

## 3. 官方 MCP Registry（只登记元数据，免费）

```bash
# 先发布到 PyPI（包名 open-jyotish-mcp），再：
brew install mcp-publisher       # 或下载 release 二进制
mcp-publisher login github       # 浏览器授权
mcp-publisher publish            # 读取仓库根目录的 server.json
```

`server.json` 里同时声明了 PyPI stdio 包和 HF 远程端点；发布前把
`remotes[0].url` 换成你的真实域名、`name` 换成你的 GitHub 用户名。

## 4. Glama / Smithery 目录（收录，免费）

- Glama：<https://glama.ai/mcp/servers> → Add Server，填 GitHub 仓库
- Smithery：2026-10-31 起**已停止托管**，只剩目录收录

## 5. 安全与合规

- 公开实例建议加 `X-API-Key` 或放在 Cloudflare Access 后面；出生时间+经纬度是强个人信息
- AGPL-3.0：公网提供服务须提供源码链接（`server_info` 与文档里都给）
- Swiss Ephemeris 星历文件按 Astrodienst 双许可使用（本项目走 AGPL 一侧）

## 6. 回滚

```bash
# HF Space
git push space --delete main   # 或删 Space
# 本地
pip uninstall open-jyotish-mcp
```
