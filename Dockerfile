# ==========================================
# Stage 1: Builder
# ==========================================
FROM python:3.13.9-slim AS builder

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

COPY pyproject.toml uv.lock README.md ./

# 依存ライブラリのみインストール
RUN uv sync --frozen --no-dev --no-install-project --compile

COPY src src

# プロジェクト本体をインストール
RUN uv sync --frozen --no-dev --compile

# ==========================================
# Stage 2: Runner
# ==========================================
FROM python:3.13.9-slim

WORKDIR /app

# builderステージで作った仮想環境をコピー
COPY --from=builder /app/.venv /app/.venv

# ソースコード等をコピー
COPY src src
COPY pyproject.toml .

# パスを通す
ENV PATH="/app/.venv/bin:$PATH"

CMD ["serve"]
