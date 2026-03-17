from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from ailtir_mcp.auth import current_token
from ailtir_mcp.mcp import AppContext


@pytest.fixture
def mock_s3() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_http() -> httpx.AsyncClient:
    # respx intercepts calls on this client inside individual tests.
    return httpx.AsyncClient(base_url="http://test-mcp-api")


@pytest.fixture
def app_context(mock_http: httpx.AsyncClient, mock_s3: MagicMock) -> AppContext:
    return AppContext(http=mock_http, s3=mock_s3)


@pytest.fixture
def mock_ctx(app_context: AppContext) -> MagicMock:
    ctx = MagicMock()
    ctx.info = AsyncMock()
    ctx.debug = AsyncMock()
    ctx.error = AsyncMock()
    ctx.report_progress = AsyncMock()
    ctx.request_context.lifespan_context = app_context
    return ctx


@pytest.fixture(autouse=True)
def set_current_token() -> None:  # type: ignore[return]
    token = current_token.set("test-token-abc123")
    yield  # type: ignore[misc]
    current_token.reset(token)
