from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from ailtir_mcp.auth import _bearer_token
from ailtir_mcp.mcp import AppContext


@pytest.fixture(autouse=True)
def reset_bearer_token() -> None:
    _bearer_token.set(None)


@pytest.fixture
def mock_http() -> httpx.AsyncClient:
    # respx intercepts calls on this client inside individual tests.
    return httpx.AsyncClient(base_url="http://test-mcp-api")


@pytest.fixture
def mock_god() -> httpx.AsyncClient:
    # respx intercepts calls on this client inside individual tests.
    return httpx.AsyncClient(
        base_url="http://test-god", headers={"Authorization": "Bearer test-god-token"}
    )


@pytest.fixture
def app_context(mock_http: httpx.AsyncClient, mock_god: httpx.AsyncClient) -> AppContext:
    return AppContext(http=mock_http, god=mock_god)


@pytest.fixture
def mock_ctx(app_context: AppContext) -> MagicMock:
    ctx = MagicMock()
    ctx.info = AsyncMock()
    ctx.debug = AsyncMock()
    ctx.error = AsyncMock()
    ctx.report_progress = AsyncMock()
    ctx.request_context.lifespan_context = app_context
    return ctx
