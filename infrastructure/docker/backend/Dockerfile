FROM ghcr.io/astral-sh/uv:0.11.29 AS uv

FROM python:3.12.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:${PATH}"

RUN groupadd --system pentagon5 \
    && useradd --system --gid pentagon5 --home-dir /app pentagon5

WORKDIR /app

COPY --from=uv /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock README.md ./
COPY backend ./backend
COPY services/authentication ./services/authentication
COPY services/api-gateway ./services/api-gateway

RUN uv sync --locked --no-dev --no-editable \
    && chown -R pentagon5:pentagon5 /app

USER pentagon5

EXPOSE 8000

ENTRYPOINT ["uvicorn"]
