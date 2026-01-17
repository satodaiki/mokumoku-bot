# ==========================================
# Stage 1: Builder
# ==========================================
FROM python:3.13.11-slim AS builder

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

COPY pyproject.toml uv.lock README.md ./

# Python 3.13.11 を指定して依存ライブラリのみインストール
RUN uv sync --frozen --no-dev --no-install-project --compile

COPY src src

# プロジェクト本体をインストール
RUN uv sync --frozen --no-dev --compile

# ==========================================
# Stage 2: Runner
# ==========================================
FROM python:3.13.11-slim

WORKDIR /app

# builderステージで作った仮想環境をコピー
COPY --from=builder /app/.venv /app/.venv

# ソースコード等をコピー
COPY src src
COPY pyproject.toml .

# .venvのpythonリンクを修正
RUN rm -f /app/.venv/bin/python /app/.venv/bin/python3 && \
    ln -s /usr/local/bin/python /app/.venv/bin/python && \
    ln -s /usr/local/bin/python /app/.venv/bin/python3

# パスを通す
ENV PATH="/app/.venv/bin:$PATH"

CMD ["serve"]
