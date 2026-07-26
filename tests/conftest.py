"""Root conftest — set required env vars before any app module is imported."""

import os

os.environ.setdefault("AILTIR_MCP_API_TOKEN", "test-token-abc123")
os.environ.setdefault("API_MCP_URL", "http://test-mcp-api")
os.environ.setdefault("GOD_URL", "http://test-god")
os.environ.setdefault("GOD_SERVICE_TOKEN", "test-god-token")
os.environ.setdefault("LOG_FORMAT", "console")
os.environ.setdefault("LOG_LEVEL", "INFO")
os.environ.setdefault("MCP_HOST", "0.0.0.0")  # noqa: S104 - test-only bind configuration
os.environ.setdefault("MCP_PORT", "8000")
os.environ.setdefault("MCP_MOUNT_PATH", "/ailtir-mcp")
