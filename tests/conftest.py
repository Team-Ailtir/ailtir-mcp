"""Root conftest — set required env vars before any app module is imported."""

import os

os.environ.setdefault("ROOT_PATH", "/ailtir-mcp")
