FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends git curl && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

COPY pyproject.toml .
COPY uv.lock .

RUN \
  --mount=type=secret,id=UV_INDEX_URL \
  export UV_INDEX_URL=$(cat /run/secrets/UV_INDEX_URL) && \
  uv sync --frozen --no-dev

COPY src/ ./src/

EXPOSE 8000

ENV PYTHONPATH=src

CMD ["uv", "run", "--frozen", "--no-dev", "python", "-m", "ailtir_mcp.server"]
