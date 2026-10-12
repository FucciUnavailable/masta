# syntax=docker/dockerfile:1

# --- frontend: build the SPA that `masta serve` hosts -------------------------
FROM node:24-slim AS web
WORKDIR /app/web
RUN npm install -g pnpm@10
COPY web/package.json web/pnpm-lock.yaml ./
RUN --mount=type=cache,target=/root/.local/share/pnpm/store \
    pnpm install --frozen-lockfile
COPY web/ ./
RUN pnpm build

# --- backend: resolve the locked Python environment ---------------------------
FROM python:3.12-slim AS python
COPY --from=ghcr.io/astral-sh/uv:0.12 /uv /bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never
WORKDIR /app
# Dependencies first, so editing source doesn't invalidate this layer.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --extra web --no-install-project
COPY README.md ./
COPY src/ ./src/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --extra web

# --- runtime ------------------------------------------------------------------
FROM python:3.12-slim
RUN useradd --create-home --uid 1000 masta \
    && mkdir /data \
    && chown masta:masta /data
# masta finds the bundled coaches and the built UI relative to the source tree, so the
# image keeps the repo layout under /app (the project is installed in editable mode).
WORKDIR /app
COPY --from=python /app/ ./
COPY examples/ ./examples/
COPY --from=web /app/web/dist/ ./web/dist/

# Everything masta writes (database, config.toml, your coaches) lives under /data.
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    MASTA_CONFIG_DIR=/data/config \
    MASTA_DATA_DIR=/data
VOLUME /data
USER masta
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=2)"]
CMD ["masta", "serve", "--host", "0.0.0.0", "--port", "8000"]
