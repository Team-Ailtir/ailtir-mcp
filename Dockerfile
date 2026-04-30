FROM python:3.13-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir uv
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen
COPY src/ ./src/
ENV MCP_MOUNT_PATH=/ailtir-mcp
EXPOSE 8000
CMD ["uv", "run", "--no-dev", "ailtir-mcp-http"]
