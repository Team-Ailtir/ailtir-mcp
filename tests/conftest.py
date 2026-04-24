"""Root conftest — set required env vars before any app module is imported."""

import os

os.environ.setdefault("AILTIR_MCP_API_TOKEN", "test-token-abc123")
