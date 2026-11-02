# syntax=docker/dockerfile:1
# Open Jyotish MCP —— 远程 deploy 用（Hugging Face Spaces / 魔搭 / 任意容器平台）
FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    MCP_TRANSPORT=streamable-http \
    MCP_HOST=0.0.0.0 \
    MCP_PORT=7860 \
    MCP_PATH=/mcp \
    MCP_STATELESS=1

# pyswisseph 2.10.3.2 没有 cp313 预编译轮子，必须现场编译 C 扩展
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src

# 星历已随包数据一起进入 src/open_jyotish_mcp/ephemeris/，装包即可用
RUN pip install --no-cache-dir .

# 非 root 运行；星历目录只读
RUN useradd -m -u 1000 mcp && chown -R mcp:mcp /app
USER mcp

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:7860/healthz', timeout=3).status==200 else 1)"

CMD ["python", "-m", "open_jyotish_mcp"]
