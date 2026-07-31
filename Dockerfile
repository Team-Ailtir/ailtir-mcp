FROM python:3.13-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir uv
COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/
RUN uv sync --no-dev --frozen
ENV MCP_MOUNT_PATH=/ailtir-mcp
EXPOSE 8000
CMD ["/app/.venv/bin/ailtir-mcp-http"]
