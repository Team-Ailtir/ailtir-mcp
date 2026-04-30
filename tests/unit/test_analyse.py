from unittest.mock import MagicMock

import httpx
import pytest
import respx
from httpx import Response

from ailtir_mcp.tools.analyse import analyse


@respx.mock
async def test_analyse_success(mock_ctx: MagicMock) -> None:
    respx.post("http://test-mcp-api/api-mcp/kbs/kb-123/analyse").mock(return_value=Response(202))

    result = await analyse("kb-123", mock_ctx)

    assert "kb-123" in result
    assert "started" in result.lower()


@respx.mock
async def test_analyse_passes_token(mock_ctx: MagicMock) -> None:
    route = respx.post("http://test-mcp-api/api-mcp/kbs/kb-123/analyse").mock(
        return_value=Response(202)
    )

    await analyse("kb-123", mock_ctx)

    assert route.calls[0].request.headers["Authorization"] == "Bearer test-token-abc123"


@respx.mock
async def test_analyse_propagates_http_error(mock_ctx: MagicMock) -> None:
    respx.post("http://test-mcp-api/api-mcp/kbs/kb-404/analyse").mock(return_value=Response(404))

    with pytest.raises(httpx.HTTPStatusError):
        await analyse("kb-404", mock_ctx)
